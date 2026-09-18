package mygit

// 인덱스의 시험 — SPEC.md §7, 6단계 "인덱스 — 스테이징의 실체".
// golden/index/ 의 세 파일은 진짜 git 이 쓴 인덱스다: 확장 없음,
// TREE 확장(git commit 뒤), 판 3(skip-worktree 가 켜진 항목).
// plain.bin 은 plain.raw 의 stat 칸을 §7.3 으로 지운 것이다.

import (
	"bytes"
	"fmt"
	"os"
	"path/filepath"
	"reflect"
	"strings"
	"syscall"
	"testing"
)

// lsStage 는 golden/index/ls-stage.txt → "모드 이름 단계\t경로" 들.
func lsStage(t *testing.T) []string {
	var out []string
	for _, line := range strings.Split(string(gread(t, "index",
		"ls-stage.txt")), "\n") {
		if line != "" {
			meta, p, _ := strings.Cut(line, "\t")
			out = append(out, meta+"\t"+unquoteC(p))
		}
	}
	return out
}

func summary(ents []*IndexEntry) []string {
	var out []string
	for _, e := range ents {
		out = append(out, fmt.Sprintf("%06o %s %d\t%s", e.Mode, e.Oid,
			e.Stage, e.Path))
	}
	return out
}

func TestS71ReadGitIndexes(t *testing.T) {
	for _, name := range []string{"plain.raw", "tree-ext.raw",
		"v3.raw"} {
		ents, err := ParseIndex(gread(t, "index", name))
		if err != nil || !reflect.DeepEqual(summary(ents),
			lsStage(t)) {
			t.Fatalf("%s: %v", name, err)
		}
		if name != "v3.raw" {
			continue
		}
		var skip []string
		for _, e := range ents {
			if e.SkipWorktree {
				skip = append(skip, e.Path)
			}
		}
		if !reflect.DeepEqual(skip, []string{"run.sh"}) {
			t.Fatal(skip)
		}
	}
	raw := gread(t, "index", "plain.raw")
	raw[len(raw)-1] ^= 1
	_, err := ParseIndex(raw)
	assertGitError(t, err)
}

func TestS72S73Write(t *testing.T) {
	raw := gread(t, "index", "plain.raw")
	ents, _ := ParseIndex(raw)
	if !bytes.Equal(SerializeIndex(ents), raw) {
		t.Fatal("왕복이 바이트까지 같아야 한다")
	}
	for _, e := range ents {
		e.CtimeS, e.CtimeNs, e.MtimeS, e.MtimeNs = 0, 0, 0, 0
		e.Dev, e.Ino, e.Uid, e.Gid = 0, 0, 0, 0
	}
	if !bytes.Equal(SerializeIndex(ents), gread(t, "index",
		"plain.bin")) {
		t.Fatal("§7.3 정규화")
	}
	ents, _ = ParseIndex(gread(t, "index", "v3.raw"))
	if data := SerializeIndex(ents); !bytes.Equal(data[4:8],
		[]byte{0, 0, 0, 2}) {
		t.Fatal("판 3 은 판 2 로 쓴다")
	}
}

func TestS72LongPathAndPadding(t *testing.T) {
	for _, n := range []int{1, 2, 7, 8, 9, 100, 4094, 4095, 4096,
		5000} {
		e := &IndexEntry{Path: "d/" + strings.Repeat("x", n),
			Oid: strings.Repeat("1", 40), Mode: 0o100644}
		data := SerializeIndex([]*IndexEntry{e})
		// 항목 길이는 8의 배수, NUL 은 1‥8 개
		body := len(data) - 12 - 20
		pad := body - 62 - len(e.Path)
		if body%8 != 0 || pad < 1 || pad > 8 {
			t.Fatal(n, body)
		}
		back, err := ParseIndex(data)
		if err != nil || back[0].Path != e.Path {
			t.Fatal(n, err)
		}
	}
}

func TestS71SortedByPathThenStage(t *testing.T) {
	var ents []*IndexEntry
	for _, ps := range []struct {
		p string
		s int
	}{{"b", 0}, {"a/x", 0}, {"a-b", 0}, {"c", 3}, {"c", 1}, {"c", 2}} {
		ents = append(ents, &IndexEntry{Path: ps.p, Stage: ps.s,
			Oid: strings.Repeat("1", 40), Mode: 0o100644})
	}
	back, _ := ParseIndex(SerializeIndex(ents))
	var got []string
	for _, e := range back {
		got = append(got, fmt.Sprintf("%s:%d", e.Path, e.Stage))
	}
	want := []string{"a-b:0", "a/x:0", "b:0", "c:1", "c:2", "c:3"}
	if !reflect.DeepEqual(got, want) {
		t.Fatal(got)
	}
}

func TestS72ExecBitAndSize(t *testing.T) {
	p := filepath.Join(t.TempDir(), "run.sh")
	os.WriteFile(p, []byte("#!/bin/sh\n"), 0o644)
	os.Chmod(p, 0o755)
	e, err := EntryFromStat("run.sh", p, strings.Repeat("2", 40))
	if err != nil || e.Mode != 0o100755 || e.Size != 10 {
		t.Fatal(e, err)
	}
	os.Chmod(p, 0o644)
	e, _ = EntryFromStat("run.sh", p, strings.Repeat("2", 40))
	var st syscall.Stat_t
	syscall.Stat(p, &st)
	if e.Mode != 0o100644 || e.MtimeS != uint32(st.Mtim.Sec) ||
		e.MtimeNs != uint32(st.Mtim.Nsec) {
		t.Fatal(e)
	}
}

func TestS74WriteAndReadBack(t *testing.T) {
	g := filepath.Join(t.TempDir(), ".git")
	os.MkdirAll(g, 0o755)
	if ents, err := ReadIndex(g); err != nil || len(ents) != 0 {
		t.Fatal(ents, err)
	}
	e := &IndexEntry{Path: "a", Oid: strings.Repeat("3", 40),
		Mode: 0o100644}
	if err := WriteIndex(g, []*IndexEntry{e}); err != nil {
		t.Fatal(err)
	}
	ents, _ := ReadIndex(g)
	if !reflect.DeepEqual(summary(ents), []string{"100644 " +
		strings.Repeat("3", 40) + " 0\ta"}) {
		t.Fatal(summary(ents))
	}
	if _, err := os.Stat(filepath.Join(g, "index.lock")); err == nil {
		t.Fatal("index.lock 이 남았다")
	}
}
