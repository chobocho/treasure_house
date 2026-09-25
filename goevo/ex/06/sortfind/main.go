// 슬라이드 p6-v119-sortfind — sort.Find, Go 1.19
package main

import (
	"fmt"
	"sort"
	"strings"
)

func main() {
	names := []string{"ada", "go", "rust", "zig"}
	for _, x := range []string{"go", "java"} {
		// Search: only a position; equality is checked by hand.
		i := sort.SearchStrings(names, x)
		hit := i < len(names) && names[i] == x

		// Find: cmp returns <0, 0, >0 like strings.Compare.
		j, found := sort.Find(len(names), func(k int) int {
			return strings.Compare(x, names[k])
		})
		fmt.Println(x, i, hit, "|", j, found)
	}
}
