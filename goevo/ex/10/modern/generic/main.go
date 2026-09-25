// 슬라이드 p10-modern-3 — 단어 세기, 1.18 의 제네릭
package main

import (
	"fmt"
	"sort"
	"strings"
)

type pair[K comparable] struct {
	key   K
	count int
}

// Tally counts any comparable values, not just strings.
func Tally[K comparable](xs []K) map[K]int {
	m := make(map[K]int)
	for _, x := range xs {
		m[x]++
	}
	return m
}

const text = "go is fun and go is fast and go is simple"

func main() {
	var ps []pair[string]
	for w, c := range Tally(strings.Fields(text)) {
		ps = append(ps, pair[string]{w, c})
	}
	sort.Slice(ps, func(i, j int) bool {
		if ps[i].count != ps[j].count {
			return ps[i].count > ps[j].count
		}
		return ps[i].key < ps[j].key
	})
	for i := 0; i < 3 && i < len(ps); i++ {
		fmt.Println(ps[i].key, ps[i].count)
	}
}
