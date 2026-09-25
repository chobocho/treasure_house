// 슬라이드 p7-v121-clear — 내장 함수 clear, Go 1.21
package main

import (
	"fmt"
	"math"
)

func main() {
	m := map[float64]string{1: "one"}
	m[math.NaN()] = "nan"
	for k := range m {
		delete(m, k) // NaN != NaN: this key cannot be deleted
	}
	fmt.Println("after delete loop:", len(m))
	clear(m)
	fmt.Println("after clear:", len(m))

	s := []int{1, 2, 3}
	clear(s) // zeroes the elements, keeps the length
	fmt.Println(s, len(s))
}
