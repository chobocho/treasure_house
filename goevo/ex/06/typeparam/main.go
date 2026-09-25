// 슬라이드 p6-v118-typeparam — 타입 매개변수 목록과 인스턴스화, Go 1.18
package main

import (
	"fmt"
	"strconv"
)

// Map has two type parameters: S for the input, T for the output.
func Map[S, T any](s []S, f func(S) T) []T {
	r := make([]T, 0, len(s))
	for _, v := range s {
		r = append(r, f(v))
	}
	return r
}

func main() {
	// Explicit type arguments, like the draft's Reverse(int)(s).
	a := Map[int, string]([]int{1, 2, 3}, strconv.Itoa)

	// Instantiation without a call gives an ordinary function value.
	itoa := Map[int, string]
	fmt.Printf("%q %T\n", a, itoa)

	// Usually the compiler infers S and T from the arguments.
	b := Map([]string{"4", "5"}, func(s string) int {
		n, _ := strconv.Atoi(s)
		return n * 10
	})
	fmt.Println(b)
}
