// 슬라이드 p10-modern-1 — 단어 세기, Go 1 의 문체
package main

import (
	"fmt"
	"sort"
	"strings"
)

type pair struct {
	word  string
	count int
}

type byCount []pair

func (p byCount) Len() int      { return len(p) }
func (p byCount) Swap(i, j int) { p[i], p[j] = p[j], p[i] }
func (p byCount) Less(i, j int) bool {
	if p[i].count != p[j].count {
		return p[i].count > p[j].count
	}
	return p[i].word < p[j].word
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
	sort.Sort(byCount(ps))
	for i := 0; i < 3 && i < len(ps); i++ {
		fmt.Println(ps[i].word, ps[i].count)
	}
}
