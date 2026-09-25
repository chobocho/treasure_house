// 슬라이드 p10-modern-5 — 단어 세기, 1.23 의 이터레이터
package main

import (
	"cmp"
	"fmt"
	"maps"
	"slices"
	"strings"
)

const text = "go is fun and go is fast and go is simple"

func main() {
	counts := make(map[string]int)
	for _, w := range strings.Fields(text) {
		counts[w]++
	}
	words := slices.Sorted(maps.Keys(counts)) // ties stay alphabetical
	slices.SortStableFunc(words, func(a, b string) int {
		return cmp.Compare(counts[b], counts[a])
	})
	for _, w := range words[:min(3, len(words))] {
		fmt.Println(w, counts[w])
	}
}
