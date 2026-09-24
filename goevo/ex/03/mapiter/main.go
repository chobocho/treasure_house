// 슬라이드 p3-v13-mapiter — 작은 맵도 순회 순서가 무작위, Go 1.3
package main

import (
	"fmt"
	"sort"
	"strings"
)

func order(m map[string]int) string {
	var keys []string
	for k := range m {
		keys = append(keys, k)
	}
	return strings.Join(keys, ",")
}

func main() {
	small := map[string]int{"a": 1, "b": 2, "c": 3} // <= 8 entries

	seen := map[string]bool{}
	for i := 0; i < 100; i++ {
		seen[order(small)] = true
	}
	fmt.Println("more than one order in 100 runs:", len(seen) > 1)

	// if the order matters, sort the keys yourself
	var keys []string
	for k := range small {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	fmt.Println("sorted:", keys)
}
