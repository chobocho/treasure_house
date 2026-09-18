package mygit

// zlib 겉옷과 느슨한 객체의 시험 — SPEC.md §3 · §4.1 · §4.6, 2단계.
// golden/objects 는 git 이 쓴 파일(고정·동적 허프만), golden/stored 는
// C++ 이 쓸 저장 블록 꼴(git 이 fsck --strict 로 받아들인 것).

import (
	"bytes"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"testing"
)

const helloID = "ce013625030ba8dba906f756967f9e9ca394464a"

func splitRaw(raw []byte) (string, int, []byte) {
	head, body, _ := bytes.Cut(raw, []byte{0})
	t, n, _ := bytes.Cut(head, []byte(" "))
	k, _ := strconv.Atoi(string(n))
	return string(t), k, body
}

// assertGitError 는 진짜 GitError 인가 — 껍데기의 코드 99 는 거짓 초록.
func assertGitError(t *testing.T, err error) *GitError {
	t.Helper()
	var ge *GitError
	if !errors.As(err, &ge) {
		t.Fatalf("GitError 가 아니다: %v", err)
	}
	if ge.Code == 99 {
		t.Fatalf("not implemented")
	}
	return ge
}

func TestS3InflateGitObjects(t *testing.T) {
	btypes := map[string]bool{}
	for _, r := range gtsv(t, "objects", "objects.tsv") {
		raw, err := Decompress(gread(t, "objects", r["id"]))
		if err != nil {
			t.Fatal(err)
		}
		typ, n, body := splitRaw(raw)
		if typ != r["type"] || fmt.Sprint(n) != r["size"] ||
			len(body) != n {
			t.Errorf("%s: %s %d", r["id"], typ, n)
		}
		if HashObject(typ, body) != r["id"] {
			t.Errorf("이름이 다르다: %s", r["id"])
		}
		btypes[r["btype"]] = true
	}
	if !btypes["1"] || !btypes["2"] {
		t.Fatal("고정·동적 허프만이 다 있어야 한다")
	}
}

func TestS3StoredBlocks(t *testing.T) {
	ents, _ := os.ReadDir(filepath.Join(goldenDir, "stored"))
	for _, e := range ents {
		raw, err := Decompress(gread(t, "stored", e.Name()))
		if err != nil {
			t.Fatal(err)
		}
		_, n, body := splitRaw(raw)
		if len(body) != n {
			t.Errorf("%s", e.Name())
		}
	}
}

func TestS3RoundTripAndPrefix(t *testing.T) {
	for _, d := range [][]byte{{}, []byte("x"),
		makeRecipe(t, "counter:70000")} {
		got, err := Decompress(Compress(d))
		if err != nil || !bytes.Equal(got, d) {
			t.Fatalf("왕복 %d", len(d))
		}
	}
	a, b := Compress([]byte("first stream")), Compress([]byte("second"))
	data := append(append([]byte("JUNK"), a...), b...)
	out, used, err := DecompressPrefix(data, 4)
	if err != nil || string(out) != "first stream" || used != len(a) {
		t.Fatalf("%q %d %v", out, used, err)
	}
	out, used, _ = DecompressPrefix(data, 4+used)
	if string(out) != "second" || used != len(b) {
		t.Fatalf("%q %d", out, used)
	}
	bad := append([]byte(nil), gread(t, "objects", helloID)...)
	bad[len(bad)-1] ^= 0xff
	_, err = Decompress(bad)
	assertGitError(t, err)
	if Adler32([]byte("Wikipedia")) != 0x11e60398 || Adler32(nil) != 1 {
		t.Fatal("adler32")
	}
}

func tempGitdir(t *testing.T) string {
	g := filepath.Join(t.TempDir(), ".git")
	os.MkdirAll(filepath.Join(g, "objects", "pack"), 0o755)
	return g
}

func plant(t *testing.T, g, oid string) {
	d := filepath.Join(g, "objects", oid[:2])
	os.MkdirAll(d, 0o755)
	os.WriteFile(filepath.Join(d, oid[2:]), gread(t, "objects", oid),
		0o644)
}

func TestS46WriteReadFind(t *testing.T) {
	if HashObject("tree", nil) !=
		"4b825dc642cb6eb9a060e54bf8d69288fbee4904" {
		t.Fatal("빈 트리")
	}
	g := tempGitdir(t)
	oid, err := WriteObject(g, "blob", []byte("hello\n"))
	if err != nil || oid != helloID {
		t.Fatal(oid, err)
	}
	if _, err := WriteObject(g, "blob", []byte("hello\n")); err != nil {
		t.Fatal("두 번째 쓰기", err)
	}
	raw, _ := os.ReadFile(ObjectPath(g, oid))
	plain, _ := Decompress(raw)
	if string(plain) != "blob 6\x00hello\n" {
		t.Fatalf("%q", plain)
	}
	rows := gtsv(t, "objects", "objects.tsv")
	for _, r := range rows {
		plant(t, g, r["id"])
		typ, body, err := ReadObject(g, r["id"])
		if err != nil || typ != r["type"] ||
			fmt.Sprint(len(body)) != r["size"] {
			t.Errorf("%s %v", r["id"], err)
		}
		if f, _ := FindObject(g, r["id"][:7]); f != r["id"] {
			t.Errorf("앞부분 %s", r["id"])
		}
	}
	if f, _ := FindObject(g, "ffffff"); f != "" {
		t.Fatal("없는 것")
	}
	_, _, err = ReadObject(g, strings.Repeat("1234567890", 4))
	assertGitError(t, err)
}

func TestS46SizeMismatchAndAmbiguous(t *testing.T) {
	g := tempGitdir(t)
	p := ObjectPath(g, helloID)
	os.MkdirAll(filepath.Dir(p), 0o755)
	os.WriteFile(p, Compress([]byte("blob 7\x00hello\n")), 0o644)
	_, _, err := ReadObject(g, helloID)
	assertGitError(t, err)
	seen := map[string][]byte{}
	for k := 0; ; k++ {
		body := []byte(fmt.Sprintf("%d\n", k))
		oid := HashObject("blob", body)
		if prev, ok := seen[oid[:4]]; ok {
			WriteObject(g, "blob", prev)
			WriteObject(g, "blob", body)
			_, err := FindObject(g, oid[:4])
			assertGitError(t, err)
			return
		}
		seen[oid[:4]] = body
	}
}
