// 슬라이드 p10-modern-4 — 단어 세기, 1.21–1.22 의 slices·cmp·min
package main

import (
	"cmp"
	"fmt"
	"slices"
	"strings"
)

type pair struct {
	word  string
	count int
}

const text = "go is fun and go is fast and go is simple"

func main() {
	counts := make(map[string]int)
	for _, w := range strings.Fields(text) {
		counts[w]++
	}
	var ps []pair
	for w, c := range counts {
		ps = append(ps, pair{w, c})
	}
	slices.SortFunc(ps, func(a, b pair) int {
		return cmp.Or(cmp.Compare(b.count, a.count),
			strings.Compare(a.word, b.word))
	})
	for _, p := range ps[:min(3, len(ps))] {
		fmt.Println(p.word, p.count)
	}
}
