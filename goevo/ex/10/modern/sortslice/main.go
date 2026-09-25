// 슬라이드 p10-modern-2 — 단어 세기, 1.8 의 sort.Slice
package main

import (
	"fmt"
	"sort"
	"strings"
)

const text = "go is fun and go is fast and go is simple"

func main() {
	counts := make(map[string]int)
	for _, w := range strings.Fields(text) {
		counts[w]++
	}
	type pair struct {
		word  string
		count int
	}
	var ps []pair
	for w, c := range counts {
		ps = append(ps, pair{w, c})
	}
	sort.Slice(ps, func(i, j int) bool {
		if ps[i].count != ps[j].count {
			return ps[i].count > ps[j].count
		}
		return ps[i].word < ps[j].word
	})
	for i := 0; i < 3 && i < len(ps); i++ {
		fmt.Println(ps[i].word, ps[i].count)
	}
}
