package mygit

// 작업 트리 바꾸기의 시험 — SPEC.md §9.3, 9단계 "checkout · switch".
// 큰 오라클은 golden/scen/checkout.scn 이다. 여기서는 장면이 직접 보지
// 않는 두 가지 — 파일이 없어져 비게 된 디렉터리가 지워지는가, 실행
// 비트가 작업 트리에 살아나는가 — 를 본다. git 도 둘 다 그렇게 한다.

import (
	"os"
	"path/filepath"
	"testing"
)

type repo struct{ *sandbox }

func newRepo(t *testing.T) repo {
	s := newSandbox(t, false)
	for k, v := range map[string]string{"GIT_AUTHOR_NAME": "A",
		"GIT_AUTHOR_EMAIL":   "a@x",
		"GIT_AUTHOR_DATE":    "1700000000 +0900",
		"GIT_COMMITTER_NAME": "C", "GIT_COMMITTER_EMAIL": "c@x",
		"GIT_COMMITTER_DATE": "1700000000 +0900"} {
		s.env[k] = v
	}
	r := repo{s}
	r.ok("init")
	return r
}

func (r repo) ok(args ...string) string {
	r.t.Helper()
	code, out, err := r.mygit(args...)
	if code != 0 {
		r.t.Fatalf("%v: %d %q %q", args, code, out, err)
	}
	return out
}

func (r repo) write(rel, data string, mode os.FileMode) {
	p := filepath.Join(r.root, rel)
	os.MkdirAll(filepath.Dir(p), 0o755)
	os.WriteFile(p, []byte(data), mode)
	os.Chmod(p, mode)
}

func TestS93EmptiedDirectoriesAreRemoved(t *testing.T) {
	r := newRepo(t)
	r.write("keep", "k\n", 0o644)
	r.ok("add", ".")
	r.ok("commit", "-m", "base")
	r.ok("switch", "-c", "deep")
	r.write("a/b/c.txt", "c\n", 0o644)
	r.ok("add", ".")
	r.ok("commit", "-m", "deep")
	r.ok("switch", "main")
	if _, err := os.Stat(filepath.Join(r.root, "a")); err == nil {
		t.Fatal("빈 디렉터리가 남았다")
	}
	r.ok("switch", "deep")
	b, _ := os.ReadFile(filepath.Join(r.root, "a", "b", "c.txt"))
	if string(b) != "c\n" {
		t.Fatalf("%q", b)
	}
}

func TestS93ExecBitIsWritten(t *testing.T) {
	r := newRepo(t)
	r.write("run", "#!/bin/sh\n", 0o755)
	r.ok("add", ".")
	r.ok("commit", "-m", "x")
	r.ok("switch", "-c", "side")
	os.Remove(filepath.Join(r.root, "run"))
	r.ok("add", ".")
	r.ok("commit", "-m", "gone")
	r.ok("switch", "main")
	st, err := os.Stat(filepath.Join(r.root, "run"))
	if err != nil || st.Mode()&0o100 == 0 {
		t.Fatal(st, err)
	}
}

func TestS93StatusIsCleanAfterSwitch(t *testing.T) {
	r := newRepo(t)
	r.write("f", "1\n", 0o644)
	r.ok("add", ".")
	r.ok("commit", "-m", "one")
	r.ok("switch", "-c", "b2")
	r.write("f", "2\n", 0o644)
	r.write("g/h", "h\n", 0o644)
	r.ok("add", ".")
	r.ok("commit", "-m", "two")
	for _, name := range []string{"main", "b2", "main"} {
		r.ok("switch", name)
		if out := r.ok("status"); out != "" {
			t.Fatalf("%s: %q", name, out)
		}
	}
}
