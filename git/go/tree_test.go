package mygit

// tree 의 시험 — SPEC.md §4.3 · §8.2, 4단계 "정렬 규칙이 전부다".
// 오라클은 golden/trees/ — 경우마다 진짜 git 이 인덱스에 올린 목록
// (<경우>.tsv), write-tree 의 이름(trees.tsv), ls-tree -r -t 의
// 출력(<경우>.ls).

import (
	"bytes"
	"path/filepath"
	"reflect"
	"strings"
	"testing"
)

func entriesOf(t *testing.T, c string) []PathEntry {
	var out []PathEntry
	for _, line := range strings.Split(string(gread(t, "trees",
		c+".tsv")), "\n") {
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}
		f := strings.SplitN(line, "\t", 3)
		out = append(out, PathEntry{f[0], f[1], f[2]})
	}
	return out
}

// unquoteC 는 git 이 C 식으로 감싼 경로를 바이트로 되돌린다(시험
// 전용). \t \n \" \\ 와 세 자리 8진 \ooo 만 나온다(SPEC.md §8.2).
func unquoteC(p string) string {
	if !strings.HasPrefix(p, "\"") {
		return p
	}
	s := p[1 : len(p)-1]
	esc := map[byte]byte{'a': 7, 'b': 8, 't': 9, 'n': 10, 'v': 11,
		'f': 12, 'r': 13, '"': 34, '\\': 92}
	var out []byte
	for i := 0; i < len(s); i++ {
		if s[i] != '\\' {
			out = append(out, s[i])
		} else if e, ok := esc[s[i+1]]; ok {
			out = append(out, e)
			i++
		} else {
			v := (s[i+1]-'0')*64 + (s[i+2]-'0')*8 + (s[i+3] - '0')
			out = append(out, v)
			i += 3
		}
	}
	return string(out)
}

func TestS43TwelveTreesHaveGitNames(t *testing.T) {
	cases := gtsv(t, "trees", "trees.tsv")
	if len(cases) != 12 {
		t.Fatal(len(cases))
	}
	for _, r := range cases {
		g := tempGitdir(t)
		ents := entriesOf(t, r["case"])
		got, err := WriteTree(g, ents)
		if err != nil || got != r["tree"] {
			t.Fatalf("%s: %s %v", r["case"], got, err)
		}
		for _, line := range strings.Split(string(gread(t, "trees",
			r["case"]+".ls")), "\n") {
			meta := strings.Fields(strings.Split(line, "\t")[0])
			if len(meta) == 3 && meta[1] == "tree" {
				if typ, _, err := ReadObject(g,
					meta[2]); typ != "tree" {
					t.Errorf("%s: %v", line, err)
				}
			}
		}
		flat, err := FlattenTree(g, got, "")
		if err != nil || !reflect.DeepEqual(flat, ents) {
			t.Errorf("펼치기 %s: %v", r["case"], err)
		}
	}
}

func TestS43DirectorySortsAsIfEndedInSlash(t *testing.T) {
	z := strings.Repeat("0", 40)
	body := SerializeTree([]TreeEntry{{"100644", "ab", z},
		{"40000", "a", z}, {"100644", "a=b", z}, {"100644", "a.b", z},
		{"100644", "a-b", z}})
	ents, _ := ParseTree(body)
	var names []string
	for _, e := range ents {
		names = append(names, e.Name)
	}
	want := []string{"a-b", "a.b", "a", "a=b", "ab"}
	if !reflect.DeepEqual(names, want) {
		t.Fatal(names)
	}
	// 이름만으로 정렬하면 a 가 맨 앞 — 규칙이 왜 있는지 보여 준다
	if !(TreeEntryKey("100644", "a-b") < TreeEntryKey(Dir, "a")) ||
		!(TreeEntryKey("100644", "a") < TreeEntryKey("100644",
			"a-b")) {
		t.Fatal("열쇠")
	}
	body = SerializeTree([]TreeEntry{{Dir, "d", strings.Repeat("1",
		40)}})
	if !bytes.HasPrefix(body, []byte("40000 d\x00")) {
		t.Fatal("모드에 0 을 붙이지 않는다")
	}
	if _, err := ParseTree([]byte("100644 x\x00abc")); err == nil {
		t.Fatal("끊긴 몸")
	} else {
		assertGitError(t, err)
	}
}

func TestS43RoundTripOnGitTrees(t *testing.T) {
	n := 0
	for _, r := range gtsv(t, "objects", "objects.tsv") {
		if r["type"] != "tree" {
			continue
		}
		body := bodyOf(t, r["id"])
		ents, err := ParseTree(body)
		if err != nil || !bytes.Equal(SerializeTree(ents), body) {
			t.Errorf("%s %v", r["id"], err)
		}
		n++
	}
	if n < 2 {
		t.Fatal(n)
	}
}

func TestS82Quoting(t *testing.T) {
	for _, c := range []struct {
		in    string
		space bool
		want  string
	}{{"plain.txt", false, "plain.txt"}, {"sp ace", false, "sp ace"},
		{"sp ace", true, `"sp ace"`}, {"tab\tx", false, `"tab\tx"`},
		{`q"uote`, false, `"q\"uote"`},
		{`back\slash`, false, `"back\\slash"`},
		{"한글.txt", false, `"\355\225\234\352\270\200.txt"`},
		{"del\x7f", false, `"del\177"`}} {
		if got := QuotePath(c.in, c.space); got != c.want {
			t.Errorf("%q → %s", c.in, got)
		}
	}
}

func TestS9CatFileTreeMatchesLsTree(t *testing.T) {
	for _, r := range gtsv(t, "trees", "trees.tsv") {
		s := newSandbox(t, true)
		g := filepath.Join(s.root, ".git")
		if _, err := WriteTree(g, entriesOf(t, r["case"])); err != nil {
			t.Fatal(err)
		}
		want := ""
		for _, line := range strings.Split(string(gread(t, "trees",
			r["case"]+".ls")), "\n") {
			_, p, ok := strings.Cut(line, "\t")
			if ok && !strings.Contains(unquoteC(p), "/") {
				want += line + "\n"
			}
		}
		code, out, _ := s.mygit("cat-file", "-p", r["tree"])
		if code != 0 || out != want {
			t.Errorf("%s:\n%s", r["case"], out)
		}
	}
}
