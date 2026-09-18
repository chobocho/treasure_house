package mygit

// 3-way 파일 합치기의 시험 — SPEC.md §12.3, 10단계.
// 큰 오라클은 golden/scen/merge-*.scn 14장면이다. 여기서는 Merge3
// 하나를 따로 부른다 — 장면의 세 판을 그대로 넣고, 장면에서 git 이
// 남긴 파일 내용과 같은지 본다. 규칙마다 한 장면이 증거다.

import "testing"

func merge3Case(t *testing.T, base, ours, theirs string) (string, int) {
	text, n := Merge3(makeRecipe(t, base), makeRecipe(t, ours),
		makeRecipe(t, theirs), "t")
	return string(text), n
}

func TestS123Merge3(t *testing.T) {
	for _, c := range []struct {
		name, base, ours, theirs, want string
		n                              int
	}{
		// merge-adjacent.scn — 둘째 줄과 셋째 줄을 따로 고쳐도 충돌
		{"adjacent", `text:a\nb\nc\nd\n`, `text:a\nB\nc\nd\n`,
			`text:a\nb\nC\nd\n`,
			"a\n<<<<<<< HEAD\nB\nc\n=======\nb\nC\n>>>>>>> t\nd\n", 1},
		{"one-apart", `text:a\nb\nc\nd\ne\n`, `text:a\nB\nc\nd\ne\n`,
			`text:a\nb\nc\nD\ne\n`, "a\nB\nc\nD\ne\n", 0},
		{"refine", `text:a\nb\nz\n`, `text:a\nq\nw\ne\nz\n`,
			`text:a\nq\nr\ne\nz\n`,
			"a\nq\n<<<<<<< HEAD\nw\n=======\nr\n>>>>>>> t\ne\nz\n", 1},
		{"identical", "seq:1:5", `text:1\nX\n3\n4\n5\n`,
			`text:1\nX\n3\n4\nY\n`, "1\nX\n3\n4\nY\n", 0},
	} {
		got, n := merge3Case(t, c.base, c.ours, c.theirs)
		if got != c.want || n != c.n {
			t.Errorf("%s: %d %q", c.name, n, got)
		}
	}
	// 사이가 바뀌지 않은 줄 셋이면 붙고, 넷이면 따로
	if _, n := merge3Case(t, `text:a\nb\nm1\nm2\nm3\nd\ne\n`,
		`text:a\n1\nm1\nm2\nm3\n2\ne\n`,
		`text:a\n3\nm1\nm2\nm3\n4\ne\n`); n != 1 {
		t.Error("join-3", n)
	}
	if _, n := merge3Case(t, `text:a\nb\nm1\nm2\nm3\nm4\nd\ne\n`,
		`text:a\n1\nm1\nm2\nm3\nm4\n2\ne\n`,
		`text:a\n3\nm1\nm2\nm3\nm4\n4\ne\n`); n != 2 {
		t.Error("split-4", n)
	}
}
