package minipuppy

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func tempWorkspace(t *testing.T) (*Registry, *Workspace) {
	t.Helper()
	dir := t.TempDir()
	must(t, os.MkdirAll(filepath.Join(dir, "src"), 0o755))
	must(t, os.WriteFile(filepath.Join(dir, "src", "a.go"),
		[]byte("package main\n\nfunc hi() string { return \"안녕\" }\n"), 0o644))
	must(t, os.WriteFile(filepath.Join(dir, "src", "b.go"),
		[]byte("package main\n\nvar x = 1\n"), 0o644))
	must(t, os.MkdirAll(filepath.Join(dir, "node_modules"), 0o755))
	must(t, os.WriteFile(filepath.Join(dir, "node_modules", "junk.go"),
		[]byte("무시되어야 한다\n"), 0o644))
	r := NewRegistry()
	RegisterFileTools(r)
	ws, err := NewWorkspace(dir)
	if err != nil {
		t.Fatal(err)
	}
	ws.Yolo = true
	return r, ws
}

func must(t *testing.T, err error) {
	t.Helper()
	if err != nil {
		t.Fatal(err)
	}
}

func TestEscapeRootIsBlocked(t *testing.T) {
	r, ws := tempWorkspace(t)
	for _, bad := range []string{"../secret", "../../etc/passwd", "src/../../밖"} {
		got := r.Call(ws, "read_file", map[string]any{"path": bad}, nil, 0)
		if got.OK || !strings.Contains(got.Content, "뿌리 밖") {
			t.Fatalf("%s 가 통과했다: %+v", bad, got)
		}
	}
}

func TestWriteNeedsApprovalUnlessYolo(t *testing.T) {
	r, ws := tempWorkspace(t)
	ws.Yolo = false
	var asked [][2]string
	ws.Approver = func(action, rel string) bool {
		asked = append(asked, [2]string{action, rel})
		return false
	}
	got := r.Call(ws, "write_file",
		map[string]any{"path": "새파일.txt", "content": "x"}, nil, 0)
	if got.OK || !strings.Contains(got.Content, "거절") {
		t.Fatalf("거절했는데 써졌다: %+v", got)
	}
	if len(asked) != 1 {
		t.Fatalf("승인 창구를 %d번 거쳤다", len(asked))
	}
	if _, err := os.Stat(filepath.Join(ws.Root, "새파일.txt")); err == nil {
		t.Fatal("거절했는데 파일이 생겼다")
	}
	ws.Approver = func(string, string) bool { return true }
	got = r.Call(ws, "write_file",
		map[string]any{"path": "새파일.txt", "content": "내용"}, nil, 0)
	if !got.OK {
		t.Fatalf("승인했는데 안 써졌다: %+v", got)
	}
	raw, err := os.ReadFile(filepath.Join(ws.Root, "새파일.txt"))
	must(t, err)
	if string(raw) != "내용" {
		t.Fatalf("내용이 다르다: %q", raw)
	}
}

func TestReadFileNumbersLines(t *testing.T) {
	r, ws := tempWorkspace(t)
	got := r.Call(ws, "read_file", map[string]any{"path": "src/b.go"}, nil, 0)
	if !got.OK || !strings.HasPrefix(got.Content, "1  package main") {
		t.Fatalf("행 번호가 없다: %q", got.Content)
	}
	got = r.Call(ws, "read_file",
		map[string]any{"path": "src/b.go", "start": 3, "end": 3}, nil, 0)
	if strings.TrimSpace(got.Content) != "3  var x = 1" {
		t.Fatalf("범위가 안 잘렸다: %q", got.Content)
	}
}

func TestListSkipsJunkDirs(t *testing.T) {
	r, ws := tempWorkspace(t)
	got := r.Call(ws, "list_files", map[string]any{"pattern": "*.go"}, nil, 0)
	if !strings.Contains(got.Content, "src/a.go") {
		t.Fatalf("소스가 안 보인다: %q", got.Content)
	}
	if strings.Contains(got.Content, "node_modules") {
		t.Fatalf("잡동사니가 섞였다: %q", got.Content)
	}
}

func TestEditRefusesAmbiguousMatch(t *testing.T) {
	r, ws := tempWorkspace(t)
	path := filepath.Join(ws.Root, "dup.go")
	must(t, os.WriteFile(path, []byte("x := 1\nx := 1\n"), 0o644))
	got := r.Call(ws, "edit_file",
		map[string]any{"path": "dup.go", "find": "x := 1", "replace": "x := 2"}, nil, 0)
	if got.OK || !strings.Contains(got.Content, "2군데") {
		t.Fatalf("여러 군데인데 고쳤다: %+v", got)
	}
	raw, _ := os.ReadFile(path)
	if string(raw) != "x := 1\nx := 1\n" {
		t.Fatalf("파일이 바뀌었다: %q", raw)
	}
}

func TestEditMissingNeedleGivesHint(t *testing.T) {
	r, ws := tempWorkspace(t)
	got := r.Call(ws, "edit_file",
		map[string]any{"path": "src/a.go", "find": "없는것", "replace": "x"}, nil, 0)
	if got.OK || !strings.Contains(got.Content, "공백") {
		t.Fatalf("힌트가 없다: %+v", got)
	}
}

func TestGrepFindsLines(t *testing.T) {
	r, ws := tempWorkspace(t)
	got := r.Call(ws, "grep", map[string]any{"needle": "안녕", "pattern": "*.go"}, nil, 0)
	if !got.OK || !strings.Contains(got.Content, "src/a.go:3") {
		t.Fatalf("못 찾았다: %q", got.Content)
	}
}
