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
	return FindObject(g, name)
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
