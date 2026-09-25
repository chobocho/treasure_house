// 슬라이드 p7-v121-infer2 — 서로 다른 종류의 무형 상수 인자, Go 1.21
package main

import (
	"cmp"
	"fmt"
)

func Larger[T cmp.Ordered](a, b T) T {
	if a > b {
		return a
	}
	return b
}

func main() {
	v := Larger(1, 2.5) // untyped int and untyped float: T = float64
	fmt.Printf("%v %T\n", v, v)
	w := Larger('a', 1) // rune and int: T = rune (int32)
	fmt.Printf("%v %T\n", w, w)
}
