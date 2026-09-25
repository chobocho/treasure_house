// 슬라이드 p7-v121-infer — 제네릭 함수를 인자로 넘길 때의 추론, Go 1.21
package main

import (
	"fmt"
	"slices"
	"strconv"
)

func Map[S ~[]E, E, R any](s S, f func(E) R) []R {
	r := make([]R, 0, len(s))
	for _, v := range s {
		r = append(r, f(v))
	}
	return r
}

func Double[T ~int | ~float64](x T) T { return 2 * x }

func Str[T ~int](x T) string { return "#" + strconv.Itoa(int(x)) }

func main() {
	nums := []int{3, 1, 2}
	fmt.Println(Map(nums, Double)) // Double[int] is inferred
	fmt.Println(Map(nums, Str))

	var sortInts func([]int) = slices.Sort // assignment infers too
	sortInts(nums)
	fmt.Println(nums)
}
