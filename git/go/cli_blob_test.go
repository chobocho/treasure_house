package mygit

// blob — hash-object · cat-file 의 시험. SPEC.md §1 · §9, 3단계.
// 오라클은 golden/objects/ 의 blob 들과 golden/errors.tsv 의 오류
// 문장이다. 명령은 Run 으로 과정 안에서 부른다.

import (
	"bytes"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"testing"
)

type sandbox struct {
	t    *testing.T
	tmp  string
	root string
	env  map[string]string
}

// newSandbox 는 임시 디렉터리. repo 면 .git 뼈대를 손으로 만든다
// (init 은 5단계의 일이다).
func newSandbox(t *testing.T, repo bool) *sandbox {
	tmp := t.TempDir()
	s := &sandbox{t: t, tmp: tmp, root: filepath.Join(tmp, "w")}
	os.MkdirAll(s.root, 0o755)
	if repo {
		g := filepath.Join(s.root, ".git")
		for _, d := range []string{"objects/pack", "refs/heads",
			"refs/tags"} {
			os.MkdirAll(filepath.Join(g, d), 0o755)
		}
		os.WriteFile(filepath.Join(g, "HEAD"),
			[]byte("ref: refs/heads/main\n"), 0o644)
	}
	// 위로 올라가다 이 덱의 저장소를 찾지 않게 (SPEC.md §1.1)
	s.env = osEnv()
	s.env["GIT_CEILING_DIRECTORIES"] = tmp
	t.Cleanup(func() {
		filepath.Walk(tmp, func(p string, i os.FileInfo,
			e error) error {
			if e == nil && !i.IsDir() {
				os.Chmod(p, 0o644)
			}
			return nil
		})
	})
	return s
}

func (s *sandbox) run(stdin []byte, args ...string) (int, string,
	string) {
	code, out, err := Run(args, s.root, s.env, stdin)
	if code == 99 {
		s.t.Fatalf("not implemented: %v", args)
	}
	return code, string(out), string(err)
}

func (s *sandbox) mygit(args ...string) (int, string, string) {
	return s.run([]byte{}, args...)
}

func (s *sandbox) put(name string, data []byte) {
	os.WriteFile(filepath.Join(s.root, name), data, 0o644)
}

func bodyOf(t *testing.T, oid string) []byte {
	raw, err := Decompress(gread(t, "objects", oid))
	if err != nil {
		t.Fatal(err)
	}
	_, body, _ := bytes.Cut(raw, []byte{0})
	return body
}

func errRow(t *testing.T, cmd string) (string, int) {
	for _, r := range gtsv(t, "errors.tsv") {
		if r["command"] == cmd {
			n, _ := strconv.Atoi(r["exit"])
			return r["stderr-first-line"], n
		}
	}
	t.Fatalf("errors.tsv 에 없다: %s", cmd)
	return "", 0
}

func firstLine(s string) string {
	l, _, _ := strings.Cut(s, "\n")
	return l
}

func TestS9HashObjectGoldenBlobs(t *testing.T) {
	s := newSandbox(t, true)
	n := 0
	for _, r := range gtsv(t, "objects", "objects.tsv") {
		if r["type"] != "blob" {
			continue
		}
		s.put("f", bodyOf(t, r["id"]))
		code, out, err := s.mygit("hash-object", "f")
		if code != 0 || out != r["id"]+"\n" || err != "" {
			t.Errorf("%s: %d %q %q", r["id"], code, out, err)
		}
		n++
	}
	if n < 3 {
		t.Fatal(n)
	}
}

func TestS9HashObjectStdinAndType(t *testing.T) {
	s := newSandbox(t, true)
	if _, out, _ := s.run([]byte("hello\n"), "hash-object",
		"--stdin"); out != helloID+"\n" {
		t.Fatal(out)
	}
	empty := "4b825dc642cb6eb9a060e54bf8d69288fbee4904\n"
	if _, out, _ := s.mygit("hash-object", "-t", "tree",
		"--stdin"); out != empty {
		t.Fatal(out)
	}
}

func TestS9WriteThenReadBack(t *testing.T) {
	s := newSandbox(t, true)
	data := makeRecipe(t, "counter:5000")
	s.put("f", data)
	_, out, _ := s.mygit("hash-object", "-w", "f")
	oid := strings.TrimSpace(out)
	for _, c := range [][3]string{{"-t", oid, "blob\n"},
		{"-s", oid, "5000\n"}, {"-p", oid, string(data)},
		{"-p", oid[:7], string(data)}} {
		code, out, err := s.mygit("cat-file", c[0], c[1])
		if code != 0 || out != c[2] || err != "" {
			t.Errorf("%v: %d %q", c[:2], code, err)
		}
	}
}

func TestS14HashObjectMissingFile(t *testing.T) {
	s := newSandbox(t, true)
	want, exit := errRow(t, "hash-object nope")
	code, _, err := s.mygit("hash-object", "nope")
	if firstLine(err) != want || code != exit {
		t.Fatalf("%d %q", code, err)
	}
}

func TestS9CatFileCommitTagBlob(t *testing.T) {
	s := newSandbox(t, true)
	g := filepath.Join(s.root, ".git")
	for _, r := range gtsv(t, "objects", "objects.tsv") {
		if r["type"] == "tree" {
			continue
		}
		plant(t, g, r["id"])
		code, out, _ := s.mygit("cat-file", "-p", r["id"])
		if code != 0 || out != string(bodyOf(t, r["id"])) {
			t.Errorf("%s", r["id"])
		}
		if _, out, _ = s.mygit("cat-file", "-t",
			r["id"]); out != r["type"]+"\n" {
			t.Errorf("%s: %q", r["id"], out)
		}
	}
}

func TestS14CatFileNotValid(t *testing.T) {
	s := newSandbox(t, true)
	want, exit := errRow(t, "cat-file -p nope")
	code, _, err := s.mygit("cat-file", "-p", "nope")
	if firstLine(err) != want || code != exit {
		t.Fatalf("%d %q", code, err)
	}
}

func TestS14OutsideRepo(t *testing.T) {
	s := newSandbox(t, false)
	want, exit := errRow(t, "status")
	code, _, err := s.mygit("cat-file", "-t", "abcd")
	if firstLine(err) != want || code != exit {
		t.Fatalf("%d %q", code, err)
	}
	s.put("f", []byte("hello\n"))
	if code, _, _ := s.mygit("hash-object", "f"); code != 0 {
		t.Fatal("hash-object 는 저장소가 없어도 된다(§1.1)")
	}
	code, _, err = s.mygit("frobnicate")
	if code != 1 ||
		err != "mygit: 'frobnicate' is not a mygit command.\n" {
		t.Fatalf("%d %q", code, err)
	}
}
