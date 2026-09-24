// 슬라이드 p5-v112-bits — 올림수가 있는 덧셈과 128비트 곱, Go 1.12
package main

import (
	"fmt"
	"math"
	"math/bits"
)

func main() {
	// 64-bit add that reports the carry out of the top bit.
	sum, carry := bits.Add64(math.MaxUint64, 1, 0)
	fmt.Println("Add64:", sum, "carry", carry)

	// 64x64 -> 128-bit product as (hi, lo).
	hi, lo := bits.Mul64(1<<63, 6)
	fmt.Println("Mul64:", hi, lo)

	// Divide the 128-bit value back.
	q, r := bits.Div64(hi, lo, 6)
	fmt.Println("Div64:", q == 1<<63, r)
}
