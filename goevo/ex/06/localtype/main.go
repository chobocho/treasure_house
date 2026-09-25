// 슬라이드 p6-v120-localtype — 제네릭 함수 안의 타입 선언, Go 1.20
package main

import (
	"fmt"
	"sort"
)

// Top returns the n most frequent values. The helper type lives
// inside the generic function: the 1.18 compiler could not do that.
func Top[T comparable](xs []T, n int) []T {
	type entry struct {
		val   T
		count int
	}
	counts := map[T]int{}
	var order []entry
	for _, x := range xs {
		if counts[x] == 0 {
			order = append(order, entry{val: x})
		}
		counts[x]++
	}
	for i := range order {
		order[i].count = counts[order[i].val]
	}
	sort.SliceStable(order, func(i, j int) bool {
		return order[i].count > order[j].count
	})
	var r []T
	for i := 0; i < n && i < len(order); i++ {
		r = append(r, order[i].val)
	}
	return r
}

func main() {
	fmt.Println(Top([]string{"a", "b", "b", "c", "b", "c"}, 2))
	fmt.Println(Top([]int{7, 7, 1}, 5))
}
