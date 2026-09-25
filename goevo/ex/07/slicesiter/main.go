// 슬라이드 p7-v123-slicesiter — slices·maps 의 반복자 함수, Go 1.23
package main

import (
	"fmt"
	"maps"
	"slices"
)

func main() {
	s := []string{"c", "a", "b"}
	for i, v := range slices.Backward(s) {
		fmt.Print(i, v, " ")
	}
	fmt.Println()

	ages := map[string]int{"cy": 40, "ana": 31, "bo": 25}
	names := slices.Sorted(maps.Keys(ages)) // a sorted snapshot
	fmt.Println(names)

	copied := maps.Collect(maps.All(ages)) // copy via iterators
	vals := slices.Collect(maps.Values(map[int]int{1: 9}))
	fmt.Println(len(copied), vals)

	for c := range slices.Chunk([]int{1, 2, 3, 4, 5}, 2) {
		fmt.Print(c, " ")
	}
	fmt.Println()
	fmt.Println(slices.AppendSeq([]string{"z"}, slices.Values(s)))
}
