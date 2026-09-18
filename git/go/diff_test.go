package mygit

// diff 의 시험 — SPEC.md §11, 8단계 "diff — Myers 알고리즘".
// golden/diff/ 는 진짜 `git -c diff.indentHeuristic=false diff
// --no-index` 의 출력이다. agree 30쌍은 바이트까지 같아야 하고, tie
// 3쌍은 git 이 같은 길이의 다른 편집 스크립트를 고르는 쌍이다 —
// 거기서는 지운 줄·끼운 줄의 수가 같고 출력은 달라야 한다(§11.2).

import (
	"os"
	"path/filepath"
	"reflect"
	"strconv"
	"strings"
	"testing"
)

func runPair(t *testing.T, s *sandbox, stem string) (int, string,
	string) {
	for _, ext := range []string{".a", ".b"} {
		os.WriteFile(filepath.Join(s.root, stem+ext),
			gread(t, "diff", stem+ext), 0o644)
	}
	return s.mygit("diff", "--no-index", stem+".a", stem+".b")
}

func TestS11AgreePairsAreByteIdentical(t *testing.T) {
	s := newSandbox(t, false)
	rows := gtsv(t, "diff", "agree.tsv")
	if len(rows) != 30 {
		t.Fatal(len(rows))
	}
	for _, r := range rows {
		code, out, err := runPair(t, s, r["name"])
		want := string(gread(t, "diff", r["name"]+".diff"))
		exit, _ := strconv.Atoi(r["exit"])
		if code != exit || out != want || err != "" {
			t.Errorf("%s: %d %q\n%s", r["name"], code, err, out)
		}
	}
}

func TestS112TiePairsSameSizeDifferentChoice(t *testing.T) {
	s := newSandbox(t, false)
	rows := gtsv(t, "diff", "tie.tsv")
	if len(rows) != 3 {
		t.Fatal(len(rows))
	}
	for _, r := range rows {
		_, out, _ := runPair(t, s, r["name"])
		minus, plus := 0, 0
		for _, l := range strings.Split(out, "\n") {
			switch {
			case strings.HasPrefix(l, "---"),
				strings.HasPrefix(l, "+++"):
			case strings.HasPrefix(l, "-"):
				minus++
			case strings.HasPrefix(l, "+"):
				plus++
			}
		}
		if strconv.Itoa(minus) != r["minus"] ||
			strconv.Itoa(plus) != r["plus"] {
			t.Errorf("%s: -%d +%d", r["name"], minus, plus)
		}
		if out == string(gread(t, "diff", r["name"]+".diff")) {
			t.Errorf("%s — 분류가 틀렸다", r["name"])
		}
	}
}

func TestS11Pieces(t *testing.T) {
	if !reflect.DeepEqual(SplitLines([]byte("a\nb\nc")),
		[]string{"a\n", "b\n", "c"}) || len(SplitLines(nil)) != 0 ||
		!reflect.DeepEqual(SplitLines([]byte("\n")),
			[]string{"\n"}) {
		t.Fatal("줄은 줄바꿈을 품는다")
	}
	// Myers 논문 그림 1 의 예 — 가장 짧은 편집 스크립트는 5
	ra, rb := Myers(SplitLines([]byte("a\nb\nc\na\nb\nb\na\n")),
		SplitLines([]byte("c\nb\na\nb\na\nc\n")))
	n := 0
	for _, f := range append(ra, rb...) {
		if f {
			n++
		}
	}
	if n != 5 {
		t.Fatal(n)
	}
	x := SplitLines([]byte("x\n"))
	if !strings.HasPrefix(string(UnifiedDiff(x, nil)),
		"@@ -1 +0,0 @@\n") || !strings.HasPrefix(string(UnifiedDiff(
		nil, SplitLines([]byte("x\ny\n")))), "@@ -0,0 +1,2 @@\n") {
		t.Fatal("덩어리 머리")
	}
	if len(UnifiedDiff(x, x)) != 0 {
		t.Fatal("같으면 덩어리가 없다")
	}
}
