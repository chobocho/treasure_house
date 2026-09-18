package mygit

// 팩의 시험 — SPEC.md §13, 11단계 "packfile — 읽기, 그다음 쓰기".
// golden/pack/ 은 진짜 git 이 쓴 팩 둘이다 — ofs(repack 이 쓴,
// OFS_DELTA)와 ref(pack-objects 가 쓴, REF_DELTA). .verify 는 git
// verify-pack -v, .show-index 는 git show-index 의 출력이다. 가장 강한
// 시험은 git 의 팩에서 다시 만든 색인이 git 의 .idx 와 바이트까지
// 같은가다.

import (
	"bytes"
	"fmt"
	"os"
	"path/filepath"
	"reflect"
	"sort"
	"strconv"
	"strings"
	"testing"
)

var packNames = []string{"ofs", "ref"}

// showIndex 는 git show-index → "자리 이름 crc" 들, 정렬.
func showIndex(t *testing.T, name string) []string {
	var rows []string
	for _, line := range strings.Split(string(gread(t, "pack",
		name+".show-index")), "\n") {
		if f := strings.Fields(line); len(f) == 3 {
			rows = append(rows, f[0]+" "+f[1]+" "+
				strings.Trim(f[2], "()"))
		}
	}
	sort.Strings(rows)
	return rows
}

func TestS131EveryObjectAndDeltaChain(t *testing.T) {
	for _, name := range packNames {
		ents, err := ReadPack(gread(t, "pack", name+".pack"), nil)
		if err != nil {
			t.Fatal(name, err)
		}
		want := map[string][]string{}
		for _, line := range strings.Split(string(gread(t, "pack",
			name+".verify")), "\n") {
			if f := strings.Fields(line); len(f) >= 5 &&
				len(f[0]) == 40 {
				want[f[0]] = f
			}
		}
		if len(ents) != len(want) {
			t.Fatal(name, len(ents), len(want))
		}
		kinds := map[int]bool{}
		for _, e := range ents {
			f := want[e.Oid]
			// 크기 칸은 팩에 적힌 크기 — 델타면 델타의 크기(§13.3)
			size := len(e.Body)
			if e.Delta != nil {
				size = len(e.Delta)
			}
			got := []string{e.Oid, e.Type, strconv.Itoa(size)}
			if f == nil || !reflect.DeepEqual(got, f[:3]) ||
				strconv.Itoa(e.Offset) != f[4] {
				t.Errorf("%s: %v ≠ %v", name, got, f)
			}
			if len(f) > 5 && (strconv.Itoa(e.Depth) != f[5] ||
				e.Base != f[6]) {
				t.Errorf("사슬 %s", e.Oid)
			}
			if HashObject(e.Type, e.Body) != e.Oid {
				t.Errorf("몸 %s", e.Oid)
			}
			kinds[e.PackedType] = true
		}
		delta := map[string]int{"ofs": 6, "ref": 7}[name]
		if !kinds[delta] {
			t.Errorf("%s 에 델타 %d 가 없다", name, delta)
		}
	}
	data := gread(t, "pack", "ofs.pack")
	data[len(data)-1] ^= 1
	_, err := ReadPack(data, nil)
	assertGitError(t, err)
}

func TestS132IdxMatchesShowIndexAndRebuilds(t *testing.T) {
	for _, name := range packNames {
		ents, sum, err := ReadIdx(gread(t, "pack", name+".idx"))
		if err != nil {
			t.Fatal(err)
		}
		var got []string
		for _, e := range ents {
			got = append(got, fmt.Sprintf("%d %s %08x", e.Offset,
				e.Oid, e.Crc))
		}
		sort.Strings(got)
		if !reflect.DeepEqual(got, showIndex(t, name)) {
			t.Errorf("%s: %v", name, got)
		}
		data := gread(t, "pack", name+".pack")
		if !bytes.Equal(sum, data[len(data)-20:]) {
			t.Error("팩 체크섬")
		}
		pents, _ := ReadPack(data, nil)
		if !bytes.Equal(WriteIdx(pents, data[len(data)-20:]),
			gread(t, "pack", name+".idx")) {
			t.Errorf("%s: 다시 만든 색인이 git 과 다르다", name)
		}
	}
}

func TestS131DeltasFromGit(t *testing.T) {
	n := 0
	for _, name := range packNames {
		ents, _ := ReadPack(gread(t, "pack", name+".pack"), nil)
		byOid := map[string]*PackEntry{}
		for _, e := range ents {
			byOid[e.Oid] = e
		}
		for _, e := range ents {
			if e.Base == "" {
				continue
			}
			got, err := ApplyDelta(byOid[e.Base].Body, e.Delta)
			if err != nil || !bytes.Equal(got, e.Body) {
				t.Error(e.Oid, err)
			}
			n++
		}
	}
	if n == 0 {
		t.Fatal("델타가 없다")
	}
	for _, d := range [][]byte{{3, 1, 0}, {4, 1, 1, 'x'}} {
		_, err := ApplyDelta([]byte("abc"), d) // 예약 0 · 바탕 크기
		assertGitError(t, err)
	}
}

func TestS133MakeDelta(t *testing.T) {
	// SPEC.md §13.3 의 알고리즘을 손으로 따라가 얻은 바이트:
	// 크기 32 · 34, 복사(0,16), 끼움 "XY", 복사(0,16)
	base := []byte(strings.Repeat("0123456789abcdef", 2))
	target := append(append([]byte(nil), base[:16]...), "XY"...)
	target = append(target, base[16:]...)
	if !bytes.Equal(MakeDelta(base, target),
		[]byte("\x20\x22\x90\x10\x02XY\x90\x10")) {
		t.Fatalf("%q", MakeDelta(base, target))
	}
	base = makeRecipe(t, "counter:70000")
	rev := make([]byte, 5000)
	for i := range rev {
		rev[i] = base[len(base)-1-i]
	}
	for _, tg := range [][]byte{base,
		append(append(append([]byte(nil), base[:30000]...), '!'),
			base[30000:]...), {},
		bytes.Repeat([]byte("x"), 300), append(rev, base...)} {
		got, err := ApplyDelta(base, MakeDelta(base, tg))
		if err != nil || !bytes.Equal(got, tg) {
			t.Fatal(len(tg), err)
		}
	}
}

func TestS133VerifyPackIsGitVerbatim(t *testing.T) {
	r := newRepo(t)
	for _, name := range packNames {
		for _, ext := range []string{".pack", ".idx"} {
			os.WriteFile(filepath.Join(r.root, name+ext),
				gread(t, "pack", name+ext), 0o644)
		}
		if out := r.ok("verify-pack", "-v", name+".idx"); out !=
			string(gread(t, "pack", name+".verify")) {
			t.Errorf("%s:\n%s", name, out)
		}
	}
}

func TestS133UnpackAndS52ReadPacked(t *testing.T) {
	r := newRepo(t)
	g := filepath.Join(r.root, ".git")
	os.WriteFile(filepath.Join(r.root, "ofs.pack"),
		gread(t, "pack", "ofs.pack"), 0o644)
	r.ok("unpack-pack", "ofs.pack")
	for _, row := range showIndex(t, "ofs") {
		oid := strings.Fields(row)[1]
		if _, err := os.Stat(ObjectPath(g, oid)); err != nil {
			t.Error(oid)
		}
	}
	r2 := newRepo(t)
	g2 := filepath.Join(r2.root, ".git")
	for _, ext := range []string{".pack", ".idx"} {
		os.WriteFile(filepath.Join(g2, "objects", "pack", "pack-x"+ext),
			gread(t, "pack", "ofs"+ext), 0o644)
	}
	for _, row := range showIndex(t, "ofs") {
		oid := strings.Fields(row)[1]
		typ, body, err := ReadObject(g2, oid)
		if err != nil || HashObject(typ, body) != oid {
			t.Error(oid, err)
		}
		if f, _ := FindObject(g2, oid[:8]); f != oid {
			t.Error("앞부분", oid)
		}
	}
}

func packHistory(t *testing.T, delta bool) []*PackEntry {
	r := newRepo(t)
	var body strings.Builder
	for i := 0; i < 200; i++ {
		fmt.Fprintf(&body, "line %d of a growing file\n", i)
	}
	for v := 0; v < 4; v++ {
		extra := strings.Repeat(fmt.Sprintf("extra %d\n", v), v+1)
		r.write("grow.txt", body.String()+extra, 0o644)
		r.ok("add", ".")
		r.ok("commit", "-m", fmt.Sprintf("v%d", v))
	}
	args := []string{"pack-objects", ".git/objects/pack/pack"}
	if delta {
		args = []string{"pack-objects", "--delta",
			".git/objects/pack/pack"}
	}
	sha := strings.TrimSpace(r.ok(args...))
	g := filepath.Join(r.root, ".git")
	stem := filepath.Join(g, "objects", "pack", "pack-"+sha)
	data, _ := os.ReadFile(stem + ".pack")
	if fmt.Sprintf("%x", data[len(data)-20:]) != sha {
		t.Fatal("이름은 팩의 SHA-1")
	}
	ents, err := ReadPack(data, nil)
	if err != nil {
		t.Fatal(err)
	}
	raw, _ := os.ReadFile(stem + ".idx")
	idx, _, _ := ReadIdx(raw)
	var a, b []string
	for _, e := range idx {
		a = append(a, e.Oid)
	}
	for _, e := range ents {
		b = append(b, e.Oid)
	}
	sort.Strings(a)
	sort.Strings(b)
	if !reflect.DeepEqual(a, b) || !reflect.DeepEqual(b,
		AllLoose(g)) {
		t.Fatal("팩·색인·느슨한 객체가 같은 집합이어야 한다")
	}
	return ents
}

func TestS133PackObjects(t *testing.T) {
	for _, e := range packHistory(t, false) {
		if e.PackedType >= 5 {
			t.Fatal("델타 없는 팩")
		}
	}
	var depths []int
	for _, e := range packHistory(t, true) {
		if e.PackedType == 6 {
			depths = append(depths, e.Depth)
		}
	}
	sort.Ints(depths)
	// 옛 판 셋이 한 판씩 새것을 바탕으로 — 깊이 1·2·3
	if !reflect.DeepEqual(depths, []int{1, 2, 3}) {
		t.Fatal(depths)
	}
}
