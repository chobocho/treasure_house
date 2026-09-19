package mygit

// 역사 걷기·merge-base·branch -d 의 시험 — SPEC.md §9.1 · §9.2 · §10,
// 7단계. golden/dag/<역사>/git 은 진짜 git 이 만든 .git 이고,
// expect.txt 는 그 저장소에서 git 이 찍은 log·merge-base 출력이다.
// equal 은 모든 커밋의 날짜가 같고(§10.1 의 "먼저 온 것이 먼저"),
// dated 는 날짜가 모두 다르고, criss 는 가장 좋은 공통 조상이 둘이다.
// criss-equal 은 criss 와 같되 날짜가 모두 같아, 두 공통 조상의
// 차례를 인자 순서와 부모 순서가 정한다(SPEC.md §10.2).

import (
	"strconv"
	"strings"
	"testing"
)

func TestS10LogAndMergeBaseMatchGit(t *testing.T) {
	n := 0
	for _, name := range []string{
		"equal", "dated", "criss", "criss-equal"} {
		s, _ := copyDag(t, name)
		text := string(gread(t, "dag", name, "expect.txt"))
		for _, block := range strings.Split(text, "$ git ")[1:] {
			cmd, rest, _ := strings.Cut(block, "\n")
			at := strings.LastIndex(rest, "= ")
			body := rest[:at]
			code, _ := strconv.Atoi(strings.TrimSpace(rest[at+2:]))
			got, out, err := s.mygit(strings.Split(cmd, " ")...)
			if got != code || out != body {
				t.Errorf("%s: %s → %d %q %q", name, cmd, got, out, err)
			}
			n++
		}
	}
	if n < 14 {
		t.Fatal(n)
	}
}

func TestS101WalkAndIsAncestor(t *testing.T) {
	_, g := copyDag(t, "equal")
	head, _ := RevParse(g, "HEAD")
	tt, _ := RevParse(g, "t")
	order, err := WalkLog(g, []string{head})
	if err != nil || len(order) != 11 || order[0] != head {
		t.Fatal(order, err)
	}
	for _, c := range []struct {
		a, b string
		want bool
	}{{tt, head, true}, {head, tt, false}, {head, head, true}} {
		if got, err := IsAncestor(g, c.a, c.b); got != c.want ||
			err != nil {
			t.Errorf("%v %v", c, err)
		}
	}
}

func TestS92BranchDelete(t *testing.T) {
	s, g := copyDag(t, "equal")
	tt, _ := RevParse(g, "t")
	code, out, err := s.mygit("branch", "-d", "t")
	if code != 0 || err != "" ||
		out != "Deleted branch t (was "+tt[:7]+").\n" {
		t.Fatalf("%d %q %q", code, out, err)
	}
	if o, _ := ResolveRef(g, "refs/heads/t"); o != "" {
		t.Fatal("남았다")
	}
	code, _, err = s.mygit("branch", "-d", "main")
	if code != 1 || err != "error: cannot delete branch 'main' "+
		"used by worktree at '"+s.root+"'\n" {
		t.Fatalf("%d %q", code, err)
	}
	s.mygit("branch", "old", "HEAD~1")
	// HEAD 를 뒤로 돌려 old 가 HEAD 에서 닿지 않게 한다
	base, _ := RevParse(g, "HEAD~2")
	SetHead(g, base)
	code, _, err = s.mygit("branch", "-d", "old")
	if code != 1 || err != "error: the branch 'old' is not fully "+
		"merged\n" {
		t.Fatalf("%d %q", code, err)
	}
}

func TestS14LogErrorsAndLimit(t *testing.T) {
	s, _ := copyDag(t, "equal")
	code, _, err := s.mygit("log", "nope")
	if code != 128 || firstLine(err) != "fatal: ambiguous argument "+
		"'nope': unknown revision or path not in the working tree." {
		t.Fatalf("%d %q", code, err)
	}
	_, out, _ := s.mygit("log", "--oneline", "-n", "3")
	if strings.Count(out, "\n") != 3 {
		t.Fatalf("%q", out)
	}
}
