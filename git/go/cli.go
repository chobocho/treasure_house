package mygit

// 명령줄 (SPEC.md §1 · §9) — 인자를 읽고, 모듈을 부르고, 찍는다.
//
// 출력은 이 파일만 한다. 다른 파일은 값을 돌려주거나 *GitError 를
// 돌려줄 뿐이다. Run 은 과정 안에서 부를 수 있는 꼴(코드, 표준 출력,
// 표준 오류)이고, cmd/mygit 은 그것을 진짜 표준 스트림에 잇는다.
//
// 명령은 commands 표에 이름으로 붙는다. 단계가 늘 때마다 한 줄씩 는다.

import (
	"bytes"
	"errors"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"sort"
	"strconv"
	"strings"
)

type cmdFunc func(ctx *Ctx, args []string) (int, error)

var commands map[string]cmdFunc

func init() {
	// init 에서 채우는 까닭: 표를 변수 초기값으로 두면 Run 을 거쳐
	// 자기를 부르는 초기화 순환으로 컴파일러가 거절한다.
	commands = map[string]cmdFunc{
		"hash-object":  cmdHashObject,
		"cat-file":     cmdCatFile,
		"init":         cmdInit,
		"commit-tree":  cmdCommitTree,
		"branch":       cmdBranch,
		"tag":          cmdTag,
		"reflog":       cmdReflog,
		"add":          cmdAdd,
		"rm":           cmdRm,
		"status":       cmdStatus,
		"write-tree":   cmdWriteTree,
		"commit":       cmdCommit,
		"log":          cmdLog,
		"merge-base":   cmdMergeBase,
		"diff":         cmdDiff,
		"switch":       cmdSwitch,
		"checkout":     cmdCheckout,
		"merge":        cmdMerge,
		"unpack-pack":  cmdUnpackPack,
		"verify-pack":  cmdVerifyPack,
		"pack-objects": cmdPackObjects,
		"clone":        cmdClone,
		"fetch-pack":   cmdFetchPack,
	}
	deleteBranch = deleteMerged
}

const notARepo = "fatal: not a git repository (or any of the parent " +
	"directories): .git"

// Ctx 는 명령 하나가 도는 동안의 문맥 — 현재 디렉터리·환경·입출력.
type Ctx struct {
	Cwd   string
	Env   map[string]string
	stdin []byte
	Out   bytes.Buffer
	Err   bytes.Buffer
	root  string
}

// ReadStdin 은 표준 입력 전부. 필요한 명령(--stdin)만 부른다 — 늘
// 읽으면 입력이 닫히지 않은 파이프에서 부를 때 멈춘다.
func (c *Ctx) ReadStdin() []byte {
	if c.stdin == nil {
		c.stdin, _ = io.ReadAll(os.Stdin)
	}
	return c.stdin
}

func (c *Ctx) say(format string, a ...any) {
	fmt.Fprintf(&c.Out, format, a...)
}

// Root 는 작업 트리의 뿌리 — .git 을 품은 디렉터리(SPEC.md §1.1).
// 현재 디렉터리부터 위로 올라가되 GIT_CEILING_DIRECTORIES 에 적힌
// 디렉터리 안으로는 올라가지 않는다. O(깊이).
func (c *Ctx) Root() (string, error) {
	if c.root != "" {
		return c.root, nil
	}
	ceil := map[string]bool{}
	for _, p := range strings.Split(c.Env["GIT_CEILING_DIRECTORIES"],
		":") {
		if p != "" {
			a, _ := filepath.Abs(p)
			ceil[a] = true
		}
	}
	for d := c.Cwd; ; {
		if st, err := os.Stat(filepath.Join(d, ".git")); err == nil &&
			st.IsDir() {
			c.root = d
			return d, nil
		}
		up := filepath.Dir(d)
		if up == d || ceil[up] {
			return "", Fail(notARepo)
		}
		d = up
	}
}

func (c *Ctx) Gitdir() (string, error) {
	r, err := c.Root()
	return filepath.Join(r, ".git"), err
}

// Path 는 명령줄의 경로 → 절대 경로(현재 디렉터리 기준).
func (c *Ctx) Path(name string) string {
	if filepath.IsAbs(name) {
		return name
	}
	return filepath.Join(c.Cwd, name)
}

// resolve 는 <rev> → 객체 이름. 없으면 "" (SPEC.md §6.2).
func resolve(ctx *Ctx, name string) (string, error) {
	g, err := ctx.Gitdir()
	if err != nil {
		return "", err
	}
	return RevParse(g, name)
}

const ambiguous = "fatal: ambiguous argument '%s': unknown revision " +
	"or path not in the working tree.\n" +
	"Use '--' to separate paths from revisions, like this:\n" +
	"'git <command> [<revision>...] -- [<file>...]'"

func ident(ctx *Ctx, who string) (string, error) {
	return IdentFromEnv(ctx.Env, who)
}

// flags 는 parseFlags 의 결과 — 켜진 옵션, 값 옵션, 나머지 인자.
type flags struct {
	on   map[string]bool
	vals map[string]string
	rest []string
}

// parseFlags 는 모르는 옵션을 SPEC.md §1.4 의 "unknown option"
// 오류로 거절한다. '--' 뒤는 전부 인자로 본다.
func parseFlags(args []string, on []string, valued ...string) (flags,
	error) {
	f := flags{on: map[string]bool{}, vals: map[string]string{}}
	has := func(xs []string, a string) bool {
		for _, x := range xs {
			if x == a {
				return true
			}
		}
		return false
	}
	for i := 0; i < len(args); i++ {
		a := args[i]
		switch {
		case a == "--":
			f.rest = append(f.rest, args[i+1:]...)
			return f, nil
		case has(valued, a):
			if i+1 >= len(args) {
				return f, Fail("fatal: mygit: option '" + a +
					"' needs a value")
			}
			i++
			f.vals[a] = args[i]
		case has(on, a):
			f.on[a] = true
		case strings.HasPrefix(a, "-") && a != "-":
			return f, Fail("fatal: mygit: unknown option '" + a + "'")
		default:
			f.rest = append(f.rest, a)
		}
	}
	return f, nil
}

// strerror 는 C 의 strerror 꼴 — Go 의 오류 문장은 소문자로 시작한다.
func strerror(err error) string {
	var pe *os.PathError
	if errors.As(err, &pe) {
		err = pe.Err
	}
	s := err.Error()
	return strings.ToUpper(s[:1]) + s[1:]
}

// ── 3단계: hash-object · cat-file ──────────────────────────────────
func cmdHashObject(ctx *Ctx, args []string) (int, error) {
	f, err := parseFlags(args, []string{"-w", "--stdin"}, "-t")
	if err != nil {
		return 0, err
	}
	typ := "blob"
	if t, ok := f.vals["-t"]; ok {
		typ = t
	}
	if !isType(typ) {
		return 0, Fail("fatal: mygit: unknown object type '" + typ +
			"'")
	}
	var bodies [][]byte
	if f.on["--stdin"] {
		bodies = append(bodies, ctx.ReadStdin())
	}
	for _, name := range f.rest {
		if f.on["--stdin"] {
			break
		}
		b, err := os.ReadFile(ctx.Path(name))
		if err != nil {
			return 0, Fail(fmt.Sprintf("fatal: could not open '%s' "+
				"for reading: %s", name, strerror(err)))
		}
		bodies = append(bodies, b)
	}
	for _, body := range bodies {
		oid := HashObject(typ, body)
		if f.on["-w"] {
			g, err := ctx.Gitdir()
			if err == nil {
				_, err = WriteObject(g, typ, body)
			}
			if err != nil {
				return 0, err
			}
		}
		ctx.say("%s\n", oid)
	}
	return 0, nil
}

// pretty 는 cat-file -p 의 몸. blob·commit·tag 는 그대로, 트리는
// 항목마다 "%06o 형식 이름\t경로" (SPEC.md §9, 따옴표는 §8.2).
func pretty(typ string, body []byte) ([]byte, error) {
	if typ != "tree" {
		return body, nil
	}
	ents, err := ParseTree(body)
	if err != nil {
		return nil, err
	}
	var buf bytes.Buffer
	for _, e := range ents {
		var mode int
		fmt.Sscanf(e.Mode, "%o", &mode)
		fmt.Fprintf(&buf, "%06o %s %s\t%s\n", mode, TypeOfMode(e.Mode),
			e.Oid, QuotePath(e.Name, false))
	}
	return buf.Bytes(), nil
}

func cmdCatFile(ctx *Ctx, args []string) (int, error) {
	f, err := parseFlags(args, []string{"-t", "-s", "-p"})
	if err != nil {
		return 0, err
	}
	if len(f.on) != 1 || len(f.rest) != 1 {
		return 0, &GitError{"usage: mygit cat-file (-t | -s | -p) " +
			"<object>", 129}
	}
	oid, err := resolve(ctx, f.rest[0])
	if err != nil {
		return 0, err
	}
	if oid == "" {
		return 0, Fail("fatal: Not a valid object name " + f.rest[0])
	}
	g, _ := ctx.Gitdir()
	typ, body, err := ReadObject(g, oid)
	if err != nil {
		return 0, err
	}
	switch {
	case f.on["-t"]:
		ctx.say("%s\n", typ)
	case f.on["-s"]:
		ctx.say("%d\n", len(body))
	default:
		text, err := pretty(typ, body)
		if err != nil {
			return 0, err
		}
		ctx.Out.Write(text)
	}
	return 0, nil
}

// ── 5단계: init · commit-tree · branch · tag · reflog ─────────────
const config = "[core]\n\trepositoryformatversion = 0\n" +
	"\tfilemode = true\n\tbare = false\n\tlogallrefupdates = true\n"

// makeRepo 는 top/.git 을 SPEC.md §5.1 의 꼴로. → (.git, 이미 있었나).
// 이미 있으면 아무것도 덮어쓰지 않는다.
func makeRepo(top string) (string, bool, error) {
	g := filepath.Join(top, ".git")
	_, err := os.Stat(g)
	again := err == nil
	for _, d := range []string{"objects/pack", "refs/heads",
		"refs/tags"} {
		if err := os.MkdirAll(filepath.Join(g, d), 0o755); err != nil {
			return "", false, err
		}
	}
	for name, text := range map[string]string{
		"HEAD": "ref: refs/heads/main\n", "config": config} {
		p := filepath.Join(g, name)
		if _, err := os.Stat(p); err != nil {
			if err := os.WriteFile(p, []byte(text), 0o644); err != nil {
				return "", false, err
			}
		}
	}
	return g, again, nil
}

func cmdInit(ctx *Ctx, args []string) (int, error) {
	f, err := parseFlags(args, nil)
	if err != nil {
		return 0, err
	}
	top := ctx.Cwd
	if len(f.rest) > 0 {
		top = ctx.Path(f.rest[0])
	}
	g, again, err := makeRepo(top)
	if err != nil {
		return 0, err
	}
	word := "Initialized empty"
	if again {
		word = "Reinitialized existing"
	}
	ctx.say("%s Git repository in %s/\n", word, g)
	return 0, nil
}

// cmdCommitTree — -p 와 -m 은 몇 번이든, 준 차례대로. 메시지는 원문
// 그대로 + 줄바꿈 — 공백 정리는 commit 명령만 한다(SPEC.md §4.4).
func cmdCommitTree(ctx *Ctx, args []string) (int, error) {
	var tree string
	var parents, msgs []string
	for i := 0; i < len(args); i++ {
		a := args[i]
		switch {
		case a == "-p" || a == "-m":
			if i+1 >= len(args) {
				return 0, Fail("fatal: mygit: option '" + a +
					"' needs a value")
			}
			i++
			if a == "-m" {
				msgs = append(msgs, args[i])
				continue
			}
			oid, err := resolve(ctx, args[i])
			if err != nil {
				return 0, err
			}
			if oid == "" {
				return 0, Fail("fatal: not a valid object name " +
					args[i])
			}
			parents = append(parents, oid)
		case strings.HasPrefix(a, "-"):
			return 0, Fail("fatal: mygit: unknown option '" + a + "'")
		default:
			tree = a
		}
	}
	if tree == "" || len(msgs) == 0 {
		return 0, &GitError{"usage: mygit commit-tree <tree> " +
			"[-p <parent>]... -m <message>...", 129}
	}
	g, err := ctx.Gitdir()
	if err != nil {
		return 0, err
	}
	oid, err := resolve(ctx, tree)
	if err == nil && oid != "" {
		oid, err = Peel(g, oid, "tree")
	}
	if err != nil {
		return 0, err
	}
	if oid == "" {
		return 0, Fail("fatal: not a valid object name " + tree)
	}
	c := &Commit{Tree: oid, Parents: parents,
		Message: strings.Join(msgs, "\n\n") + "\n"}
	if c.Author, err = ident(ctx, "AUTHOR"); err != nil {
		return 0, err
	}
	if c.Committer, err = ident(ctx, "COMMITTER"); err != nil {
		return 0, err
	}
	oid, err = WriteObject(g, "commit", SerializeCommit(c))
	if err != nil {
		return 0, err
	}
	ctx.say("%s\n", oid)
	return 0, nil
}

func listBranches(ctx *Ctx, g string) (int, error) {
	cur, head, err := ReadHead(g)
	if err != nil {
		return 0, err
	}
	if cur == "" && head != "" {
		ctx.say("* (HEAD detached at %s)\n", head[:7])
	}
	for _, r := range ListRefs(g, "refs/heads/") {
		mark := "  "
		if r.Name == cur {
			mark = "* "
		}
		ctx.say("%s%s\n", mark, strings.TrimPrefix(r.Name,
			"refs/heads/"))
	}
	return 0, nil
}

// deleteBranch 는 7단계가 채운다 — HEAD 에서 닿는지 보려면 DAG 순회가
// 있어야 한다.
var deleteBranch = func(ctx *Ctx, g string, names []string) (int,
	error) {
	return 0, NotImplemented()
}

func cmdBranch(ctx *Ctx, args []string) (int, error) {
	f, err := parseFlags(args, []string{"-d"})
	if err != nil {
		return 0, err
	}
	g, err := ctx.Gitdir()
	if err != nil {
		return 0, err
	}
	if f.on["-d"] {
		return deleteBranch(ctx, g, f.rest)
	}
	if len(f.rest) == 0 {
		return listBranches(ctx, g)
	}
	name := f.rest[0]
	if !ValidBranchName(name) {
		return 0, Fail("fatal: '" + name + "' is not a valid branch " +
			"name")
	}
	if o, _ := ResolveRef(g, "refs/heads/"+name); o != "" {
		return 0, Fail("fatal: a branch named '" + name +
			"' already exists")
	}
	start := "HEAD"
	if len(f.rest) > 1 {
		start = f.rest[1]
	}
	oid, err := resolve(ctx, start)
	if err == nil && oid != "" {
		oid, err = Peel(g, oid, "commit")
	}
	if err != nil {
		return 0, err
	}
	if oid == "" {
		return 0, Fail("fatal: not a valid object name: '" + start +
			"'")
	}
	who, err := ident(ctx, "COMMITTER")
	if err != nil {
		return 0, err
	}
	return 0, UpdateRef(g, "refs/heads/"+name, oid, "",
		"branch: Created from "+start, who)
}

func cmdTag(ctx *Ctx, args []string) (int, error) {
	f, err := parseFlags(args, []string{"-a"}, "-m")
	if err != nil {
		return 0, err
	}
	g, err := ctx.Gitdir()
	if err != nil {
		return 0, err
	}
	if len(f.rest) == 0 {
		for _, r := range ListRefs(g, "refs/tags/") {
			ctx.say("%s\n", strings.TrimPrefix(r.Name, "refs/tags/"))
		}
		return 0, nil
	}
	name, target := f.rest[0], "HEAD"
	if len(f.rest) > 1 {
		target = f.rest[1]
	}
	if ReadRef(g, "refs/tags/"+name) != nil {
		return 0, Fail("fatal: tag '" + name + "' already exists")
	}
	oid, err := resolve(ctx, target)
	if err != nil {
		return 0, err
	}
	if oid == "" {
		return 0, Fail("fatal: Failed to resolve '" + target +
			"' as a valid ref.")
	}
	if msg, ok := f.vals["-m"]; ok || f.on["-a"] {
		typ, _, err := ReadObject(g, oid)
		if err != nil {
			return 0, err
		}
		who, err := ident(ctx, "COMMITTER")
		if err != nil {
			return 0, err
		}
		body := SerializeTag(oid, typ, name, who, CleanupMessage(msg))
		if oid, err = WriteObject(g, "tag", body); err != nil {
			return 0, err
		}
	}
	// 태그는 reflog 를 남기지 않는다 — logallrefupdates 는 브랜치와
	// HEAD 만 기록한다(git 과 같다)
	path := filepath.Join(g, "refs", "tags", name)
	os.MkdirAll(filepath.Dir(path), 0o755)
	return 0, os.WriteFile(path, []byte(oid+"\n"), 0o644)
}

// cmdReflog 는 새것부터 '<7글자> <ref>@{n}: <메시지>' (SPEC.md §6.3).
func cmdReflog(ctx *Ctx, args []string) (int, error) {
	f, err := parseFlags(args, nil)
	if err != nil {
		return 0, err
	}
	g, err := ctx.Gitdir()
	if err != nil {
		return 0, err
	}
	var rest []string
	for _, a := range f.rest {
		if a != "show" {
			rest = append(rest, a)
		}
	}
	name := "HEAD"
	if len(rest) > 0 {
		name = rest[0]
	}
	log := ""
	for _, cand := range []string{name, "refs/heads/" + name} {
		if _, err := os.Stat(filepath.Join(g, "logs",
			cand)); err == nil {
			log = cand
			break
		}
	}
	if log == "" {
		if name == "HEAD" {
			return 0, nil
		}
		return 0, Fail(fmt.Sprintf(ambiguous, name))
	}
	ents := ReadReflog(g, log)
	for k := range ents {
		e := ents[len(ents)-1-k]
		ctx.say("%s %s@{%d}: %s\n", e.New[:7], name, k, e.Msg)
	}
	return 0, nil
}

// ── 6단계: add · rm --cached · status · write-tree · commit ────────

// relPath 는 명령줄 경로 → 작업 트리 뿌리에서의 경로(” 은 뿌리).
func relPath(ctx *Ctx, spec string) (string, error) {
	root, err := ctx.Root()
	if err != nil {
		return "", err
	}
	p, err := filepath.Rel(root, ctx.Path(spec))
	if err != nil {
		return "", err
	}
	if p == "." {
		return "", nil
	}
	return filepath.ToSlash(p), nil
}

func under(path, rel string) bool {
	return rel == "" || path == rel || strings.HasPrefix(path, rel+"/")
}

// cmdAdd 는 pathspec 아래의 파일을 올리고, 사라진 파일은 뺀다(§9).
// 모든 pathspec 을 먼저 검사한다 — 하나라도 맞는 것이 없으면 아무것도
// 바꾸지 않고 멈춘다(git 과 같다).
func cmdAdd(ctx *Ctx, args []string) (int, error) {
	f, err := parseFlags(args, nil)
	if err != nil {
		return 0, err
	}
	root, err := ctx.Root()
	if err != nil {
		return 0, err
	}
	g, _ := ctx.Gitdir()
	ents, err := ReadIndex(g)
	if err != nil {
		return 0, err
	}
	files := WalkWorktree(root)
	type hit struct {
		files []string
		idx   map[string]bool
	}
	var plan []hit
	for _, spec := range f.rest {
		rel, err := relPath(ctx, spec)
		if err != nil {
			return 0, err
		}
		h := hit{idx: map[string]bool{}}
		for _, p := range files {
			if under(p, rel) {
				h.files = append(h.files, p)
			}
		}
		for _, e := range ents {
			if under(e.Path, rel) {
				h.idx[e.Path] = true
			}
		}
		if len(h.files) == 0 && len(h.idx) == 0 {
			return 0, Fail("fatal: pathspec '" + spec +
				"' did not match any files")
		}
		plan = append(plan, h)
	}
	byPath := map[string][]*IndexEntry{}
	for _, e := range ents {
		byPath[e.Path] = append(byPath[e.Path], e)
	}
	for _, h := range plan {
		for _, p := range h.files {
			full := filepath.Join(root, p)
			data, err := os.ReadFile(full)
			if err != nil {
				return 0, err
			}
			oid, err := WriteObject(g, "blob", data)
			if err != nil {
				return 0, err
			}
			e, err := EntryFromStat(p, full, oid)
			if err != nil {
				return 0, err
			}
			byPath[p] = []*IndexEntry{e}
			delete(h.idx, p)
		}
		for p := range h.idx {
			delete(byPath, p)
		}
	}
	var out []*IndexEntry
	for _, es := range byPath {
		out = append(out, es...)
	}
	return 0, WriteIndex(g, out)
}

func cmdRm(ctx *Ctx, args []string) (int, error) {
	f, err := parseFlags(args, []string{"--cached"})
	if err != nil {
		return 0, err
	}
	if !f.on["--cached"] {
		return 0, Fail("fatal: mygit: only rm --cached is supported")
	}
	g, err := ctx.Gitdir()
	if err != nil {
		return 0, err
	}
	ents, err := ReadIndex(g)
	if err != nil {
		return 0, err
	}
	have, gone := map[string]bool{}, map[string]bool{}
	for _, e := range ents {
		have[e.Path] = true
	}
	for _, spec := range f.rest {
		rel, err := relPath(ctx, spec)
		if err != nil {
			return 0, err
		}
		if !have[rel] {
			return 0, Fail("fatal: pathspec '" + spec +
				"' did not match any files")
		}
		gone[rel] = true
	}
	for _, p := range sortedKeys(gone) {
		ctx.say("rm '%s'\n", p)
	}
	var keep []*IndexEntry
	for _, e := range ents {
		if !gone[e.Path] {
			keep = append(keep, e)
		}
	}
	return 0, WriteIndex(g, keep)
}

func cmdStatus(ctx *Ctx, args []string) (int, error) {
	if _, err := parseFlags(args, []string{"--porcelain", "-s",
		"--short"}); err != nil {
		return 0, err
	}
	root, err := ctx.Root()
	if err != nil {
		return 0, err
	}
	rows, err := Status(root, filepath.Join(root, ".git"))
	for _, r := range rows {
		ctx.say("%s\n", r)
	}
	return 0, err
}

// indexTree 는 인덱스(단계 0) → 트리 이름. 충돌 경로가 있으면 쓸 수
// 없다.
func indexTree(g string) (string, error) {
	ents, err := ReadIndex(g)
	if err != nil {
		return "", err
	}
	var pes []PathEntry
	for _, e := range ents {
		if e.Stage > 0 {
			return "", Fail("error: Committing is not possible " +
				"because you have unmerged files.\n" +
				"fatal: Exiting because of an unresolved conflict.")
		}
		pes = append(pes, PathEntry{fmt.Sprintf("%o", e.Mode), e.Oid,
			e.Path})
	}
	return WriteTree(g, pes)
}

func cmdWriteTree(ctx *Ctx, args []string) (int, error) {
	if _, err := parseFlags(args, nil); err != nil {
		return 0, err
	}
	g, err := ctx.Gitdir()
	if err != nil {
		return 0, err
	}
	t, err := indexTree(g)
	if err != nil {
		return 0, err
	}
	ctx.say("%s\n", t)
	return 0, nil
}

// cmdCommit 은 트리를 쓰고, 커밋하고, 브랜치를 옮긴다(SPEC.md §9 ·
// §6.3). 부모는 HEAD 와, 머지를 마무리하는 중이면 MERGE_HEAD. 출력은
// git 의 요약 첫 줄만 — Author 줄과 변경 통계는 줄임이다.
func cmdCommit(ctx *Ctx, args []string) (int, error) {
	var msgs []string
	for i := 0; i < len(args); i++ {
		if args[i] != "-m" {
			return 0, Fail("fatal: mygit: unknown option '" +
				args[i] + "'")
		}
		i++
		if i < len(args) {
			msgs = append(msgs, args[i])
		} else {
			msgs = append(msgs, "")
		}
	}
	g, err := ctx.Gitdir()
	if err != nil {
		return 0, err
	}
	branch, head, err := ReadHead(g)
	if err != nil {
		return 0, err
	}
	mergeHead, _ := ResolveRef(g, "MERGE_HEAD")
	t, err := indexTree(g)
	if err != nil {
		return 0, err
	}
	if head != "" && mergeHead == "" {
		if ht, _ := Peel(g, head, "tree"); ht == t {
			ctx.say("nothing to commit\n")
			return 1, nil
		}
	}
	msg := CleanupMessage(strings.Join(msgs, "\n\n"))
	if msg == "" {
		return 0, &GitError{"Aborting commit due to empty commit " +
			"message.", 1}
	}
	c := &Commit{Tree: t, Message: msg}
	for _, p := range []string{head, mergeHead} {
		if p != "" {
			c.Parents = append(c.Parents, p)
		}
	}
	if c.Author, err = ident(ctx, "AUTHOR"); err != nil {
		return 0, err
	}
	if c.Committer, err = ident(ctx, "COMMITTER"); err != nil {
		return 0, err
	}
	oid, err := WriteObject(g, "commit", SerializeCommit(c))
	if err != nil {
		return 0, err
	}
	subj := SubjectOf(msg)
	kind := "commit"
	if head == "" {
		kind = "commit (initial)"
	} else if mergeHead != "" {
		kind = "commit (merge)"
	}
	target := branch
	if target == "" {
		target = "HEAD"
	}
	if err := UpdateRef(g, target, oid, head, kind+": "+subj,
		c.Committer); err != nil {
		return 0, err
	}
	for _, f := range []string{"MERGE_HEAD", "MERGE_MSG"} {
		os.Remove(filepath.Join(g, f))
	}
	where, root := "detached HEAD", ""
	if branch != "" {
		where = strings.TrimPrefix(branch, "refs/heads/")
	}
	if head == "" {
		root = " (root-commit)"
	}
	ctx.say("[%s%s %s] %s\n", where, root, oid[:7], subj)
	return 0, nil
}

// ── 7단계: log · merge-base · branch -d ─────────────────────────────

// deleteMerged 는 branch -d — HEAD 에서 닿는 브랜치만 지운다(§9.2).
func deleteMerged(ctx *Ctx, g string, names []string) (int, error) {
	cur, head, err := ReadHead(g)
	if err != nil {
		return 0, err
	}
	for _, name := range names {
		ref := "refs/heads/" + name
		oid, err := ResolveRef(g, ref)
		if err != nil {
			return 0, err
		}
		if ref == cur {
			root, _ := ctx.Root()
			return 0, &GitError{"error: cannot delete branch '" + name +
				"' used by worktree at '" + root + "'", 1}
		}
		if oid == "" {
			return 0, &GitError{"error: branch '" + name +
				"' not found.", 1}
		}
		merged := false
		if head != "" {
			if merged, err = IsAncestor(g, oid, head); err != nil {
				return 0, err
			}
		}
		if !merged {
			return 0, &GitError{"error: the branch '" + name +
				"' is not fully merged", 1}
		}
		if err := UpdateRef(g, ref, "", oid, "", ""); err != nil {
			return 0, err
		}
		ctx.say("Deleted branch %s (was %s).\n", name, oid[:7])
	}
	return 0, nil
}

// logEntry 는 커밋 하나를 git log 의 꼴로(SPEC.md §9.1).
func logEntry(g, oid string, oneline bool) (string, error) {
	_, body, err := ReadObject(g, oid)
	if err != nil {
		return "", err
	}
	c, err := ParseCommit(body)
	if err != nil {
		return "", err
	}
	if oneline {
		return oid[:7] + " " + SubjectOf(c.Message) + "\n", nil
	}
	name, mail, secs, tz, err := ParseIdent(c.Author)
	if err != nil {
		return "", err
	}
	rows := []string{"commit " + oid}
	if len(c.Parents) > 1 {
		var short []string
		for _, p := range c.Parents {
			short = append(short, p[:7])
		}
		rows = append(rows, "Merge: "+strings.Join(short, " "))
	}
	rows = append(rows, "Author: "+name+" <"+mail+">",
		"Date:   "+FormatDate(secs, tz), "")
	for _, line := range strings.Split(strings.TrimSuffix(c.Message,
		"\n"), "\n") {
		rows = append(rows, "    "+line)
	}
	return strings.Join(rows, "\n") + "\n", nil
}

func cmdLog(ctx *Ctx, args []string) (int, error) {
	f, err := parseFlags(args, []string{"--oneline"}, "-n")
	if err != nil {
		return 0, err
	}
	g, err := ctx.Gitdir()
	if err != nil {
		return 0, err
	}
	var start string
	if len(f.rest) > 0 {
		start, err = resolve(ctx, f.rest[0])
		if err == nil && start != "" {
			start, err = Peel(g, start, "commit")
		}
		if err != nil {
			return 0, err
		}
		if start == "" {
			return 0, Fail(fmt.Sprintf(ambiguous, f.rest[0]))
		}
	} else {
		var branch string
		if branch, start, err = ReadHead(g); err != nil {
			return 0, err
		}
		if start == "" {
			return 0, Fail("fatal: your current branch '" +
				strings.TrimPrefix(branch, "refs/heads/") +
				"' does not have any commits yet")
		}
	}
	order, err := WalkLog(g, []string{start})
	if err != nil {
		return 0, err
	}
	if n, ok := f.vals["-n"]; ok {
		k, _ := strconv.Atoi(n)
		order = order[:min(max(k, 0), len(order))]
	}
	sep := "\n"
	if f.on["--oneline"] {
		sep = ""
	}
	var parts []string
	for _, oid := range order {
		e, err := logEntry(g, oid, f.on["--oneline"])
		if err != nil {
			return 0, err
		}
		parts = append(parts, e)
	}
	ctx.say("%s", strings.Join(parts, sep))
	return 0, nil
}

func cmdMergeBase(ctx *Ctx, args []string) (int, error) {
	f, err := parseFlags(args, []string{"--all"})
	if err != nil {
		return 0, err
	}
	if len(f.rest) != 2 {
		return 0, &GitError{"usage: mygit merge-base [--all] <a> <b>",
			129}
	}
	g, err := ctx.Gitdir()
	if err != nil {
		return 0, err
	}
	var ids []string
	for _, name := range f.rest {
		oid, err := resolve(ctx, name)
		if err == nil && oid != "" {
			oid, err = Peel(g, oid, "commit")
		}
		if err != nil {
			return 0, err
		}
		if oid == "" {
			return 0, Fail("fatal: Not a valid object name " + name)
		}
		ids = append(ids, oid)
	}
	best, err := MergeBases(g, ids[0], ids[1])
	if err != nil {
		return 0, err
	}
	if len(best) == 0 {
		return 1, nil
	}
	if !f.on["--all"] {
		best = best[:1]
	}
	for _, oid := range best {
		ctx.say("%s\n", oid)
	}
	return 0, nil
}

// ── 8단계: diff ─────────────────────────────────────────────────────

// revTreeMap 은 <rev> 의 트리를 펼쳐 {경로: Blob}.
func revTreeMap(ctx *Ctx, g, rev string) (map[string]Blob, error) {
	oid, err := resolve(ctx, rev)
	if err == nil && oid != "" {
		oid, err = Peel(g, oid, "tree")
	}
	if err != nil {
		return nil, err
	}
	if oid == "" {
		return nil, Fail(fmt.Sprintf(ambiguous, rev))
	}
	return TreeMap(g, oid)
}

// cmdDiff 는 SPEC.md §11.5 의 네 꼴. --no-index 만 다르면 1 로
// 끝난다.
func cmdDiff(ctx *Ctx, args []string) (int, error) {
	f, err := parseFlags(args, []string{"--cached", "--no-index"})
	if err != nil {
		return 0, err
	}
	if f.on["--no-index"] {
		if len(f.rest) != 2 {
			return 0, &GitError{"usage: mygit diff --no-index <a> <b>",
				129}
		}
		text := FileDiff(f.rest[0], f.rest[1],
			DiskSide(ctx.Path(f.rest[0])),
			DiskSide(ctx.Path(f.rest[1])))
		ctx.Out.Write(text)
		if len(text) > 0 {
			return 1, nil
		}
		return 0, nil
	}
	root, err := ctx.Root()
	if err != nil {
		return 0, err
	}
	g := filepath.Join(root, ".git")
	// 두 쪽의 {경로: Blob}. 작업 트리 쪽은 disk 가 참이다.
	var a, b map[string]Blob
	disk := false
	switch {
	case len(f.rest) == 2:
		if a, err = revTreeMap(ctx, g, f.rest[0]); err != nil {
			return 0, err
		}
		if b, err = revTreeMap(ctx, g, f.rest[1]); err != nil {
			return 0, err
		}
	case len(f.rest) > 0:
		return 0, Fail(fmt.Sprintf(ambiguous, f.rest[0]))
	case f.on["--cached"]:
		t, err := headTree(g)
		if err == nil {
			a, err = TreeMap(g, t)
		}
		if err != nil {
			return 0, err
		}
		fallthrough
	default:
		ents, err := ReadIndex(g)
		if err != nil {
			return 0, err
		}
		idx, conflicted := map[string]Blob{}, map[string]bool{}
		for _, e := range ents {
			if e.Stage > 0 {
				conflicted[e.Path] = true
			} else {
				idx[e.Path] = Blob{e.Mode, e.Oid}
			}
		}
		if a != nil {
			b = idx
			break
		}
		// 작업 트리 ↔ 인덱스: 충돌 경로는 건너뛴다(줄임)
		a, b, disk = map[string]Blob{}, map[string]Blob{}, true
		for p, bl := range idx {
			if conflicted[p] {
				continue
			}
			a[p] = bl
			if s := DiskSide(filepath.Join(root, p)); s != nil {
				b[p] = Blob{s.Mode, s.Oid}
			}
		}
	}
	all := map[string]bool{}
	for p := range a {
		all[p] = true
	}
	for p := range b {
		all[p] = true
	}
	for _, p := range sortedKeys(all) {
		oa, ina := a[p]
		ob, inb := b[p]
		if ina == inb && oa == ob {
			continue
		}
		var old, new *Side
		if ina {
			if old, err = BlobSide(g, oa); err != nil {
				return 0, err
			}
		}
		switch {
		case inb && disk:
			new = DiskSide(filepath.Join(root, p))
		case inb:
			if new, err = BlobSide(g, ob); err != nil {
				return 0, err
			}
		}
		ctx.Out.Write(FileDiff(p, p, old, new))
	}
	return 0, nil
}

// ── 9단계: switch · checkout ─────────────────────────────────────────

// summaryLine 은 '<7글자> <제목>' — HEAD is now at … 의 꼬리.
func summaryLine(g, oid string) (string, error) {
	_, body, err := ReadObject(g, oid)
	if err != nil {
		return "", err
	}
	c, err := ParseCommit(body)
	if err != nil {
		return "", err
	}
	return oid[:7] + " " + SubjectOf(c.Message), nil
}

// moveHead 는 작업 트리를 oid 로 옮기고 HEAD 를 branch(또는 "" 이면
// 분리)로(SPEC.md §9.3). 안내는 표준 오류에, 남은 변경 알림은 표준
// 출력에. reflog 는 "checkout: moving from <옛> to <arg 그대로>" —
// 옛 쪽이 분리 상태면 40글자다(§6.3). fresh 는 switch -c 의 안내.
func moveHead(ctx *Ctx, branch, oid, arg string, report,
	fresh bool) (int, error) {
	root, err := ctx.Root()
	if err != nil {
		return 0, err
	}
	g := filepath.Join(root, ".git")
	oldBranch, old, err := ReadHead(g)
	if err != nil {
		return 0, err
	}
	oldTree := ""
	if old != "" {
		if oldTree, err = Peel(g, old, "tree"); err != nil {
			return 0, err
		}
	}
	newTree, err := Peel(g, oid, "tree")
	if err != nil {
		return 0, err
	}
	if err := CheckoutTree(root, g, oldTree, newTree); err != nil {
		return 0, err
	}
	// 분리 상태를 떠나되 커밋이 바뀔 때만 — 같은 커밋이면 git 도
	// 찍지 않는다
	if oldBranch == "" && old != "" && oid != old {
		line, err := summaryLine(g, old)
		if err != nil {
			return 0, err
		}
		fmt.Fprintf(&ctx.Err, "Previous HEAD position was %s\n", line)
	}
	target := branch
	if target == "" {
		target = oid
	}
	if err := SetHead(g, target); err != nil {
		return 0, err
	}
	frm := old
	if oldBranch != "" {
		frm = strings.TrimPrefix(oldBranch, "refs/heads/")
	}
	who, err := ident(ctx, "COMMITTER")
	if err != nil {
		return 0, err
	}
	if err := AppendReflog(g, "HEAD", old, oid, who,
		"checkout: moving from "+frm+" to "+arg); err != nil {
		return 0, err
	}
	if report {
		rows, err := LocalChanges(root, g, newTree)
		if err != nil {
			return 0, err
		}
		for _, r := range rows {
			ctx.say("%s\n", r)
		}
	}
	switch {
	case branch == "":
		line, err := summaryLine(g, oid)
		if err != nil {
			return 0, err
		}
		fmt.Fprintf(&ctx.Err, "HEAD is now at %s\n", line)
	case fresh:
		fmt.Fprintf(&ctx.Err, "Switched to a new branch '%s'\n", arg)
	case branch == oldBranch:
		fmt.Fprintf(&ctx.Err, "Already on '%s'\n", arg)
	default:
		fmt.Fprintf(&ctx.Err, "Switched to branch '%s'\n", arg)
	}
	return 0, nil
}

func createAndSwitch(ctx *Ctx, name, start string) (int, error) {
	g, err := ctx.Gitdir()
	if err != nil {
		return 0, err
	}
	if !ValidBranchName(name) {
		return 0, Fail("fatal: '" + name + "' is not a valid branch " +
			"name")
	}
	if o, _ := ResolveRef(g, "refs/heads/"+name); o != "" {
		return 0, Fail("fatal: a branch named '" + name +
			"' already exists")
	}
	_, old, err := ReadHead(g)
	if err != nil {
		return 0, err
	}
	if old == "" && start == "" {
		// 첫 커밋 전 — HEAD 가 가리키는 이름만 바꾼다
		if err := SetHead(g, "refs/heads/"+name); err != nil {
			return 0, err
		}
		fmt.Fprintf(&ctx.Err, "Switched to a new branch '%s'\n", name)
		return 0, nil
	}
	arg := start
	if arg == "" {
		arg = "HEAD"
	}
	oid, err := resolve(ctx, arg)
	if err == nil && oid != "" {
		oid, err = Peel(g, oid, "commit")
	}
	if err != nil {
		return 0, err
	}
	if oid == "" {
		return 0, Fail("fatal: invalid reference: " + arg)
	}
	who, err := ident(ctx, "COMMITTER")
	if err != nil {
		return 0, err
	}
	if err := UpdateRef(g, "refs/heads/"+name, oid, "",
		"branch: Created from "+arg, who); err != nil {
		return 0, err
	}
	// 지금 커밋에서 새 브랜치를 만들 때는 git 이 작업 트리를 건드리지
	// 않고 남은 변경도 알리지 않는다(golden/scen/checkout.scn)
	return moveHead(ctx, "refs/heads/"+name, oid, name, oid != old,
		true)
}

func cmdSwitch(ctx *Ctx, args []string) (int, error) {
	f, err := parseFlags(args, nil, "-c")
	if err != nil {
		return 0, err
	}
	if name, ok := f.vals["-c"]; ok {
		start := ""
		if len(f.rest) > 0 {
			start = f.rest[0]
		}
		return createAndSwitch(ctx, name, start)
	}
	if len(f.rest) != 1 {
		return 0, &GitError{"usage: mygit switch [-c] <branch>", 129}
	}
	g, err := ctx.Gitdir()
	if err != nil {
		return 0, err
	}
	name := f.rest[0]
	oid, err := ResolveRef(g, "refs/heads/"+name)
	if err != nil {
		return 0, err
	}
	if oid != "" {
		return moveHead(ctx, "refs/heads/"+name, oid, name, true,
			false)
	}
	if o, _ := resolve(ctx, name); o != "" {
		return 0, Fail("fatal: a branch is expected, got commit '" +
			name + "'")
	}
	return 0, Fail("fatal: invalid reference: " + name)
}

func cmdCheckout(ctx *Ctx, args []string) (int, error) {
	f, err := parseFlags(args, nil)
	if err != nil {
		return 0, err
	}
	if len(f.rest) != 1 {
		return 0, &GitError{"usage: mygit checkout <branch|commit>",
			129}
	}
	g, err := ctx.Gitdir()
	if err != nil {
		return 0, err
	}
	name := f.rest[0]
	oid, err := ResolveRef(g, "refs/heads/"+name)
	if err != nil {
		return 0, err
	}
	if oid != "" {
		return moveHead(ctx, "refs/heads/"+name, oid, name, true,
			false)
	}
	oid, err = resolve(ctx, name)
	if err == nil && oid != "" {
		oid, err = Peel(g, oid, "commit")
	}
	if err != nil {
		return 0, err
	}
	if oid == "" {
		return 0, &GitError{"error: pathspec '" + name +
			"' did not match any file(s) known to git", 1}
	}
	return moveHead(ctx, "", oid, name, true, false)
}

// ── 10단계: merge ────────────────────────────────────────────────────
const mygitMerge = "Merge made by mygit (3-way, no renames)."

func writeGitFile(g, name, text string) error {
	return os.WriteFile(filepath.Join(g, name), []byte(text), 0o644)
}

// isClean 은 인덱스가 HEAD 트리와 같고 추적 파일이 그대로인가
// (SPEC.md §12.1).
func isClean(root, g, head string) (bool, error) {
	t, err := Peel(g, head, "tree")
	if err != nil {
		return false, err
	}
	want, err := TreeMap(g, t)
	if err != nil {
		return false, err
	}
	ents, err := ReadIndex(g)
	if err != nil || len(ents) != len(want) {
		return false, err
	}
	for _, e := range ents {
		cur := Blob{e.Mode, e.Oid}
		if e.Stage > 0 || want[e.Path] != cur {
			return false, nil
		}
		if disk, ok := FileState(root, e.Path); !ok || disk != cur {
			return false, nil
		}
	}
	return true, nil
}

// cmdMerge 는 SPEC.md §12.1 — 이미 최신 · fast-forward · 3-way.
func cmdMerge(ctx *Ctx, args []string) (int, error) {
	f, err := parseFlags(args, nil)
	if err != nil {
		return 0, err
	}
	if len(f.rest) != 1 {
		return 0, &GitError{"usage: mygit merge <branch>", 129}
	}
	root, err := ctx.Root()
	if err != nil {
		return 0, err
	}
	g, name := filepath.Join(root, ".git"), f.rest[0]
	theirs, err := resolve(ctx, name)
	if err == nil && theirs != "" {
		theirs, err = Peel(g, theirs, "commit")
	}
	if err != nil {
		return 0, err
	}
	if theirs == "" {
		return 0, &GitError{"merge: " + name +
			" - not something we can merge", 1}
	}
	branch, head, err := ReadHead(g)
	if err != nil {
		return 0, err
	}
	if clean, err := isClean(root, g, head); err != nil {
		return 0, err
	} else if !clean {
		return 0, Fail("error: mygit: commit your local changes " +
			"before merging")
	}
	who, err := ident(ctx, "COMMITTER")
	if err != nil {
		return 0, err
	}
	target := branch
	if target == "" {
		target = "HEAD"
	}
	// git 은 이미 최신이어도 ORIG_HEAD 를 지금 HEAD 로 다시 쓴다
	// (golden/scen/merge-ff.scn 의 두 번째 merge 뒤)
	if err := writeGitFile(g, "ORIG_HEAD", head+"\n"); err != nil {
		return 0, err
	}
	if up, err := IsAncestor(g, theirs, head); err != nil || up {
		if up {
			ctx.say("Already up to date.\n")
		}
		return 0, err
	}
	oldTree, err := Peel(g, head, "tree")
	if err != nil {
		return 0, err
	}
	if ff, err := IsAncestor(g, head, theirs); err != nil {
		return 0, err
	} else if ff {
		ctx.say("Updating %s..%s\nFast-forward\n", head[:7],
			theirs[:7])
		newTree, err := Peel(g, theirs, "tree")
		if err == nil {
			err = CheckoutTree(root, g, oldTree, newTree)
		}
		if err == nil {
			err = UpdateRef(g, target, theirs, head,
				"merge "+name+": Fast-forward", who)
		}
		return 0, err
	}
	bases, err := MergeBases(g, head, theirs)
	if err != nil {
		return 0, err
	}
	if len(bases) != 1 {
		return 0, Fail(fmt.Sprintf("fatal: mygit: %d merge bases "+
			"(criss-cross) are not supported", len(bases)))
	}
	var maps [3]map[string]Blob
	for k, c := range []string{bases[0], head, theirs} {
		t, err := Peel(g, c, "tree")
		if err == nil {
			maps[k], err = TreeMap(g, t)
		}
		if err != nil {
			return 0, err
		}
	}
	result, notes, conflicts, err := MergeTrees(g, maps[0], maps[1],
		maps[2], name)
	if err != nil {
		return 0, err
	}
	if err := applyMerge(root, g, maps[1], result); err != nil {
		return 0, err
	}
	for _, line := range notes {
		ctx.say("%s\n", line)
	}
	msg := "Merge commit '" + name + "'"
	if o, _ := ResolveRef(g, "refs/heads/"+name); o != "" {
		msg = "Merge branch '" + name + "'"
	}
	if cur := strings.TrimPrefix(branch, "refs/heads/"); branch != "" &&
		cur != "main" && cur != "master" {
		msg += " into " + cur
	}
	if len(conflicts) > 0 {
		var b strings.Builder
		b.WriteString(msg + "\n\n# Conflicts:\n")
		for _, p := range conflicts {
			b.WriteString("#\t" + p + "\n")
		}
		err := writeGitFile(g, "MERGE_HEAD", theirs+"\n")
		if err == nil {
			err = writeGitFile(g, "MERGE_MSG", b.String())
		}
		if err != nil {
			return 0, err
		}
		ctx.say("Automatic merge failed; fix conflicts and then " +
			"commit the result.\n")
		return 1, nil
	}
	t, err := indexTree(g)
	if err != nil {
		return 0, err
	}
	c := &Commit{Tree: t, Parents: []string{head, theirs},
		Message: msg + "\n", Committer: who}
	if c.Author, err = ident(ctx, "AUTHOR"); err != nil {
		return 0, err
	}
	oid, err := WriteObject(g, "commit", SerializeCommit(c))
	if err != nil {
		return 0, err
	}
	if err := UpdateRef(g, target, oid, head,
		"merge "+name+": "+mygitMerge, who); err != nil {
		return 0, err
	}
	ctx.say("%s\n", mygitMerge)
	return 0, nil
}

// applyMerge 는 합친 결과를 작업 트리와 인덱스에 쓴다. 충돌 경로는
// 단계 1‥3.
func applyMerge(root, g string, ours map[string]Blob,
	result map[string]MergeResult) error {
	ents, err := ReadIndex(g)
	if err != nil {
		return err
	}
	byPath := map[string]*IndexEntry{}
	for _, e := range ents {
		byPath[e.Path] = e
	}
	var staged []*IndexEntry
	for _, p := range sortedKeys(result) {
		r := result[p]
		switch {
		case r.Gone:
			if _, ok := ours[p]; ok {
				removeFile(root, p)
			}
			delete(byPath, p)
		case r.Conflict:
			err := writeFile(root, p, r.Blob.Mode, r.Text)
			if err != nil {
				return err
			}
			delete(byPath, p)
			for k := 1; k <= 3; k++ {
				if b, ok := r.Stages[k]; ok {
					staged = append(staged, &IndexEntry{Path: p,
						Oid: b.Oid, Mode: b.Mode, Stage: k})
				}
			}
		case ours[p] != r.Blob:
			_, data, err := ReadObject(g, r.Blob.Oid)
			if err == nil {
				err = writeFile(root, p, r.Blob.Mode, data)
			}
			if err != nil {
				return err
			}
			e, err := EntryFromStat(p, filepath.Join(root, p),
				r.Blob.Oid)
			if err != nil {
				return err
			}
			byPath[p] = e
		}
	}
	for _, e := range byPath {
		staged = append(staged, e)
	}
	return WriteIndex(g, staged)
}

// ── 11단계: unpack-pack · verify-pack · pack-objects ────────────────

// cmdUnpackPack 은 팩의 객체를 전부 느슨한 객체로 푼다(§13.3).
func cmdUnpackPack(ctx *Ctx, args []string) (int, error) {
	f, err := parseFlags(args, nil)
	if err != nil {
		return 0, err
	}
	g, err := ctx.Gitdir()
	if err != nil {
		return 0, err
	}
	for _, name := range f.rest {
		data, err := os.ReadFile(ctx.Path(name))
		if err != nil {
			return 0, err
		}
		ents, err := ReadPack(data, func(o string) (string, []byte,
			error) {
			return ReadObject(g, o)
		})
		if err != nil {
			return 0, err
		}
		for _, e := range ents {
			if _, err := WriteObject(g, e.Type, e.Body); err != nil {
				return 0, err
			}
		}
	}
	return 0, nil
}

// cmdVerifyPack 은 git verify-pack -v 와 같은 출력. 색인이 팩과 맞지
// 않으면 오류.
func cmdVerifyPack(ctx *Ctx, args []string) (int, error) {
	f, err := parseFlags(args, []string{"-v"})
	if err != nil {
		return 0, err
	}
	if !f.on["-v"] || len(f.rest) != 1 ||
		!strings.HasSuffix(f.rest[0], ".idx") {
		return 0, &GitError{"usage: mygit verify-pack -v <pack>.idx",
			129}
	}
	packPath := strings.TrimSuffix(f.rest[0], ".idx") + ".pack"
	raw, err := os.ReadFile(ctx.Path(f.rest[0]))
	if err != nil {
		return 0, err
	}
	idx, sum, err := ReadIdx(raw)
	if err != nil {
		return 0, err
	}
	data, err := os.ReadFile(ctx.Path(packPath))
	if err != nil {
		return 0, err
	}
	ents, err := ReadPack(data, nil)
	if err != nil {
		return 0, err
	}
	var got, want []string
	for _, e := range ents {
		got = append(got, fmt.Sprintf("%s %d %d", e.Oid, e.Offset,
			e.Crc))
	}
	for _, e := range idx {
		want = append(want, fmt.Sprintf("%s %d %d", e.Oid, e.Offset,
			e.Crc))
	}
	sort.Strings(got)
	sort.Strings(want)
	if strings.Join(got, ",") != strings.Join(want, ",") ||
		!bytes.Equal(sum, data[len(data)-20:]) {
		return 0, Fail("fatal: mygit: " + f.rest[0] +
			" does not match " + packPath)
	}
	for _, row := range VerifyLines(ents, packPath) {
		ctx.say("%s\n", row)
	}
	return 0, nil
}

const maxDepth = 50

// packItems 는 pack-objects 가 넣을 객체들 — SPEC.md §13.3 의
// 차례(커밋 → 트리·blob 전위 순회 → 주석 태그)와 델타 고르기.
// 바탕은 같은 경로에서 바로 앞에 넣은 blob, 델타가 몸의 절반보다
// 짧을 때만.
func packItems(g string, useDelta bool) ([]PackItem, error) {
	var starts []string
	_, head, err := ReadHead(g)
	if err != nil {
		return nil, err
	}
	cands := []string{head}
	for _, r := range ListRefs(g, "refs/") {
		cands = append(cands, r.Oid)
	}
	for _, oid := range cands {
		if oid == "" {
			continue
		}
		c, err := Peel(g, oid, "commit")
		if err != nil {
			return nil, err
		}
		if c != "" {
			starts = append(starts, c)
		}
	}
	var items []PackItem
	var depth []int
	seen, last := map[string]bool{}, map[string]int{}
	add := func(typ string, body []byte, oid, path string) {
		seen[oid] = true
		base := -1
		if k, ok := last[path]; ok && useDelta && path != "" &&
			depth[k] < maxDepth {
			if 2*len(MakeDelta(items[k].Body, body)) < len(body) {
				base = k
			}
		}
		items = append(items, PackItem{typ, body, base})
		if base >= 0 {
			depth = append(depth, depth[base]+1)
		} else {
			depth = append(depth, 0)
		}
		if path != "" {
			last[path] = len(items) - 1
		}
	}
	var order []string
	if len(starts) > 0 {
		if order, err = WalkLog(g, starts); err != nil {
			return nil, err
		}
	}
	for _, c := range order {
		_, body, err := ReadObject(g, c)
		if err != nil {
			return nil, err
		}
		add("commit", body, c, "")
	}
	var visit func(t, prefix string) error
	visit = func(t, prefix string) error {
		if seen[t] {
			return nil
		}
		_, body, err := ReadObject(g, t)
		if err != nil {
			return err
		}
		add("tree", body, t, "")
		ents, err := ParseTree(body)
		if err != nil {
			return err
		}
		for _, e := range ents {
			switch {
			case e.Mode == Dir:
				err = visit(e.Oid, prefix+e.Name+"/")
			case e.Mode != "160000" && !seen[e.Oid]:
				var blob []byte
				if _, blob, err = ReadObject(g, e.Oid); err == nil {
					add("blob", blob, e.Oid, prefix+e.Name)
				}
			}
			if err != nil {
				return err
			}
		}
		return nil
	}
	for _, c := range order {
		t, err := Peel(g, c, "tree")
		if err == nil {
			err = visit(t, "")
		}
		if err != nil {
			return nil, err
		}
	}
	for _, r := range ListRefs(g, "refs/tags/") {
		typ, body, err := ReadObject(g, r.Oid)
		if err != nil {
			return nil, err
		}
		if typ == "tag" && !seen[r.Oid] {
			add("tag", body, r.Oid, "")
		}
	}
	return items, nil
}

func cmdPackObjects(ctx *Ctx, args []string) (int, error) {
	f, err := parseFlags(args, []string{"--delta"})
	if err != nil {
		return 0, err
	}
	if len(f.rest) != 1 {
		return 0, &GitError{"usage: mygit pack-objects [--delta] " +
			"<base>", 129}
	}
	g, err := ctx.Gitdir()
	if err != nil {
		return 0, err
	}
	items, err := packItems(g, f.on["--delta"])
	if err != nil {
		return 0, err
	}
	data, ents := WritePack(items)
	sha := fmt.Sprintf("%x", data[len(data)-20:])
	base := ctx.Path(f.rest[0] + "-" + sha)
	if err := os.MkdirAll(filepath.Dir(base), 0o755); err != nil {
		return 0, err
	}
	err = os.WriteFile(base+".pack", data, 0o644)
	if err == nil {
		err = os.WriteFile(base+".idx",
			WriteIdx(ents, data[len(data)-20:]), 0o644)
	}
	if err != nil {
		return 0, err
	}
	ctx.say("%s\n", sha)
	return 0, nil
}

// ── 12단계: clone · fetch-pack ──────────────────────────────────────

// cmdClone 은 멍청한 로컬 clone(SPEC.md §14.2). 안내는 표준 오류에.
func cmdClone(ctx *Ctx, args []string) (int, error) {
	f, err := parseFlags(args, nil)
	if err != nil {
		return 0, err
	}
	if len(f.rest) != 2 {
		return 0, &GitError{"usage: mygit clone <path> <dir>", 129}
	}
	src, dst := ctx.Path(f.rest[0]), ctx.Path(f.rest[1])
	if st, err := os.Stat(src); err != nil || !st.IsDir() {
		return 0, Fail("fatal: repository '" + f.rest[0] +
			"' does not exist")
	}
	who, err := ident(ctx, "COMMITTER")
	if err != nil {
		return 0, err
	}
	fmt.Fprintf(&ctx.Err, "Cloning into '%s'...\n", f.rest[1])
	if _, _, err := makeRepo(dst); err != nil {
		return 0, err
	}
	if _, err := CloneLocal(src, dst, who); err != nil {
		return 0, err
	}
	ctx.Err.WriteString("done.\n")
	return 0, nil
}

// cmdFetchPack 은 진짜 git upload-pack 과 v2 로 말해 팩을 받는다
// (SPEC.md §14.3).
func cmdFetchPack(ctx *Ctx, args []string) (int, error) {
	f, err := parseFlags(args, nil)
	if err != nil {
		return 0, err
	}
	if len(f.rest) < 2 {
		return 0, &GitError{"usage: mygit fetch-pack <path> <ref>...",
			129}
	}
	g, err := ctx.Gitdir()
	if err != nil {
		return 0, err
	}
	got, err := FetchPack(g, ctx.Path(f.rest[0]), f.rest[1:], ctx.Env,
		ctx.Env["MYGIT_PKT_LOG"])
	for _, p := range got {
		ctx.say("%s %s\n", p[0], p[1])
	}
	return 0, err
}

// ── 틀 ─────────────────────────────────────────────────────────────

// Run 은 명령 하나를 돌린다 → (종료 코드, 표준 출력, 표준 오류).
// env 가 nil 이면 지금 환경, stdin 이 nil 이면 진짜 표준 입력.
func Run(args []string, cwd string, env map[string]string,
	stdin []byte) (int, []byte, []byte) {
	ctx := &Ctx{Env: env, stdin: stdin}
	if cwd == "" {
		cwd, _ = os.Getwd()
	}
	ctx.Cwd, _ = filepath.Abs(cwd)
	if env == nil {
		ctx.Env = map[string]string{}
		for _, kv := range os.Environ() {
			k, v, _ := strings.Cut(kv, "=")
			ctx.Env[k] = v
		}
	}
	if len(args) == 0 {
		ctx.Err.WriteString("usage: mygit <command> [<args>]\n")
		return 129, ctx.Out.Bytes(), ctx.Err.Bytes()
	}
	fn := commands[args[0]]
	if fn == nil {
		fmt.Fprintf(&ctx.Err, "mygit: '%s' is not a mygit command.\n",
			args[0])
		return 1, ctx.Out.Bytes(), ctx.Err.Bytes()
	}
	code, err := fn(ctx, args[1:])
	if err != nil {
		var ge *GitError
		if errors.As(err, &ge) {
			ctx.Err.WriteString(ge.Msg + "\n")
			code = ge.Code
		} else {
			// 파일 시스템 오류 같은 뜻밖의 것 — git 처럼 fatal 128
			ctx.Err.WriteString("fatal: " + err.Error() + "\n")
			code = 128
		}
	}
	return code, ctx.Out.Bytes(), ctx.Err.Bytes()
}
