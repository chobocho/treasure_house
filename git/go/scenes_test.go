package mygit

// 장면 시험 — golden/scen/*.scn 을 mygit 으로 다시 돌린다
// (SPEC.md §16.4).
//
// 장면의 기대 출력은 진짜 git 2.55.0 이 채웠다. 같은 명령을 빈 임시
// 디렉터리에서 mygit 으로 돌리고, 명령마다 표준 출력·표준 오류·종료
// 코드를 한 글자씩 견준다. 장면은 자기에게 필요한 명령이 다 생기는
// 단계(Step)부터 켜진다. 12단계를 마치면 건너뛰는 장면이 없어야 한다.

import (
	"fmt"
	"os"
	"path/filepath"
	"reflect"
	"strconv"
	"strings"
	"testing"
)

// needs 는 장면 → 켜지는 단계 (그 장면이 쓰는 명령이 모두 생기는 단계)
var needs = map[string]int{"plumbing": 6, "status": 6, "hello": 7,
	"diff": 8, "checkout": 9, "errors": 10, "clone": 12}

func stepOf(name string) int {
	if strings.HasPrefix(name, "merge-") {
		return 10
	}
	return needs[name]
}

// splitArgs 는 SPEC.md §16.4 — 공백으로 가르고 "…" 는 한 덩어리.
func splitArgs(line string) []string {
	var args []string
	var cur *strings.Builder
	quoted := false
	for i := 0; i < len(line); i++ {
		c := line[i]
		switch {
		case quoted && c == '\\' && i+1 < len(line):
			i++
			switch line[i] {
			case 'n':
				cur.WriteByte('\n')
			case 't':
				cur.WriteByte('\t')
			default:
				cur.WriteByte(line[i])
			}
		case quoted && c == '"':
			quoted = false
		case quoted:
			cur.WriteByte(c)
		case c == '"':
			quoted = true
			if cur == nil {
				cur = &strings.Builder{}
			}
		case c == ' ' || c == '\t':
			if cur != nil {
				args = append(args, cur.String())
				cur = nil
			}
		default:
			if cur == nil {
				cur = &strings.Builder{}
			}
			cur.WriteByte(c)
		}
	}
	if cur != nil {
		args = append(args, cur.String())
	}
	return args
}

type sceneStep struct {
	line string
	want []string
}

// parseScene 은 .scn → 명령 줄과 기대 줄들. 기대 줄은 '> ' · '! ' ·
// '= ' 로 시작하거나 '%noeol' 이다.
func parseScene(text string) []sceneStep {
	var steps []sceneStep
	for _, line := range strings.Split(text, "\n") {
		if line == "" || line[0] == '#' {
			continue
		}
		p := line[:min(2, len(line))]
		if p == "> " || p == "! " || p == "= " || line == "%noeol" {
			s := &steps[len(steps)-1]
			s.want = append(s.want, line)
		} else {
			steps = append(steps, sceneStep{line, []string{}})
		}
	}
	return steps
}

// renderResult 는 실제 결과를 .scn 의 기대 줄 꼴로.
func renderResult(out, err []byte, code int) []string {
	rows := []string{}
	for _, pd := range []struct {
		prefix string
		data   []byte
	}{{"> ", out}, {"! ", err}} {
		text := string(pd.data)
		if text == "" {
			continue
		}
		body := strings.TrimSuffix(text, "\n")
		for _, l := range strings.Split(body, "\n") {
			rows = append(rows, pd.prefix+l)
		}
		if !strings.HasSuffix(text, "\n") {
			rows = append(rows, "%noeol")
		}
	}
	if code != 0 {
		rows = append(rows, fmt.Sprintf("= %d", code))
	}
	return rows
}

type scene struct {
	t         *testing.T
	root, cwd string
	env       map[string]string
}

func (s *scene) date(secs string) {
	for _, who := range []string{"AUTHOR", "COMMITTER"} {
		s.env["GIT_"+who+"_DATE"] = secs + " +0900"
	}
}

func (s *scene) gitdir() string {
	g, err := (&Ctx{Cwd: s.cwd, Env: s.env}).Gitdir()
	if err != nil {
		s.t.Fatal(err)
	}
	return g
}

// do 는 한 줄을 돌려 결과 줄들. 손질 줄은 nil.
func (s *scene) do(line string) []string {
	a := splitArgs(line)
	path := ""
	if len(a) > 1 {
		path = filepath.Join(s.cwd, a[1])
	}
	ok := func(data []byte) []string {
		return renderResult(data, nil, 0)
	}
	switch a[0] {
	case "@date":
		s.date(a[1])
	case "@cd":
		s.cwd = filepath.Join(s.root, a[1])
	case "write", "append":
		os.MkdirAll(filepath.Dir(path), 0o755)
		flag := os.O_WRONLY | os.O_CREATE | os.O_TRUNC
		if a[0] == "append" {
			flag = os.O_WRONLY | os.O_CREATE | os.O_APPEND
		}
		f, err := os.OpenFile(path, flag, 0o644)
		if err != nil {
			s.t.Fatal(err)
		}
		f.Write(makeRecipe(s.t, a[2]))
		f.Close()
	case "chmod":
		m, _ := strconv.ParseUint(a[2], 8, 32)
		os.Chmod(path, os.FileMode(m))
	case "rm":
		os.Remove(path)
	case "mkdir":
		os.MkdirAll(path, 0o755)
	case "mygit":
		var args []string
		for _, x := range a[1:] {
			args = append(args, strings.ReplaceAll(x, "<ROOT>", s.root))
		}
		code, out, err := Run(args, s.cwd, s.env, []byte{})
		return renderResult(out, err, code)
	case "cat":
		b, err := os.ReadFile(path)
		if err != nil {
			s.t.Fatal(err)
		}
		return ok(b)
	case "stage":
		ents, err := ReadIndex(s.gitdir())
		if err != nil {
			s.t.Fatal(err)
		}
		var b strings.Builder
		for _, e := range ents {
			fmt.Fprintf(&b, "%06o %s %d\t%s\n", e.Mode, e.Oid, e.Stage,
				QuotePath(e.Path, false))
		}
		return ok([]byte(b.String()))
	case "ref":
		oid, err := RevParse(s.gitdir(), a[1])
		if err != nil {
			s.t.Fatal(err)
		}
		return ok([]byte(oid + "\n"))
	default:
		s.t.Fatalf("모르는 장면 줄: %s", line)
	}
	return nil
}

func TestS164Scenes(t *testing.T) {
	ents, _ := os.ReadDir(filepath.Join(goldenDir, "scen"))
	for _, f := range ents {
		name := strings.TrimSuffix(f.Name(), ".scn")
		t.Run(name, func(t *testing.T) {
			if Step < stepOf(name) {
				t.Skipf("%d단계에서 켜진다", stepOf(name))
			}
			tmp := t.TempDir()
			root := filepath.Join(tmp, "scene")
			os.MkdirAll(root, 0o755)
			sc := &scene{t: t, root: root, cwd: root, env: osEnv()}
			for k, v := range identEnv() {
				sc.env[k] = v
			}
			sc.env["GIT_CEILING_DIRECTORIES"] = tmp
			sc.date("1700000000")
			t.Cleanup(func() { chmodAll(tmp) })
			text := string(gread(t, "scen", f.Name()))
			for k, st := range parseScene(text) {
				got := sc.do(st.line)
				want := []string{}
				for _, w := range st.want {
					want = append(want, strings.ReplaceAll(w, "<ROOT>",
						root))
				}
				if got == nil {
					got = []string{}
				}
				if !reflect.DeepEqual(got, want) {
					t.Fatalf("%s 장면 %d번째 줄: %s\n얻음 %q\n기대 %q",
						name, k, st.line, got, want)
				}
			}
		})
	}
}
