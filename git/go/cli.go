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
	"strings"
)

type cmdFunc func(ctx *Ctx, args []string) (int, error)

var commands map[string]cmdFunc

func init() {
	// init 에서 채우는 까닭: 표를 변수 초기값으로 두면 Run 을 거쳐
	// 자기를 부르는 초기화 순환으로 컴파일러가 거절한다.
	commands = map[string]cmdFunc{
		"hash-object": cmdHashObject,
		"cat-file":    cmdCatFile,
		"init":        cmdInit,
		"commit-tree": cmdCommitTree,
		"branch":      cmdBranch,
		"tag":         cmdTag,
		"reflog":      cmdReflog,
	}
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
