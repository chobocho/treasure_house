// 슬라이드 p7-v121-minmax — 내장 함수 min·max, Go 1.21
package main

import (
	"fmt"
	"math"
)

func main() {
	fmt.Println(min(3, 1, 2), max(3, 1, 2)) // any number of args
	fmt.Println(min("b", "a", "c"))         // strings compare bytewise
	fmt.Println(max(1, 2.5))                // untyped constants: 2.5

	var x int8 = 100
	fmt.Println(max(x, 7)) // 7 becomes int8

	nan := math.NaN()
	fmt.Println(min(1.0, nan), max(nan, 1.0)) // NaN wins
	fmt.Println(min(0.0, math.Copysign(0, -1)))
}
