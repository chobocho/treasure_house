package mygit

// sha1 의 시험 — SPEC.md §2 · 부록 A 1단계. 기준은 golden/sha1.tsv
// 100줄(sha1sum · git hash-object). crypto/sha1 은 증인으로만 쓴다.

import (
	"crypto/sha1"
	"fmt"
	"testing"
)

func TestS2Vectors(t *testing.T) {
	rows := gtsv(t, "sha1.tsv")
	if len(rows) != 100 {
		t.Fatalf("벡터 %d개", len(rows))
	}
	for _, r := range rows {
		data := makeRecipe(t, r["recipe"])
		if fmt.Sprint(len(data)) != r["len"] {
			t.Fatalf("%s: 길이 %d", r["name"], len(data))
		}
		if got := Sum1Hex(data); got != r["sha1"] {
			t.Errorf("%s: %s != %s", r["name"], got, r["sha1"])
		}
		head := []byte(fmt.Sprintf("blob %d\x00", len(data)))
		if got := Sum1Hex(append(head, data...)); got != r["blob"] {
			t.Errorf("%s: blob %s != %s", r["name"], got, r["blob"])
		}
	}
}

func TestS2PaddingBoundaries(t *testing.T) {
	for n := 0; n < 200; n++ {
		data := make([]byte, n)
		for i := range data {
			data[i] = byte(i * 7)
		}
		if Sum1(data) != sha1.Sum(data) {
			t.Errorf("길이 %d", n)
		}
	}
}

func TestS2Streaming(t *testing.T) {
	data := makeRecipe(t, "counter:100000")
	want := Sum1(data)
	for _, size := range []int{1, 3, 63, 64, 65, 1000, 99999} {
		h := NewSha1()
		for k := 0; k < len(data); k += size {
			end := min(k+size, len(data))
			h.Update(data[k:end])
		}
		if h.Digest() != want || h.Digest() != want {
			t.Errorf("조각 %d", size)
		}
	}
}
