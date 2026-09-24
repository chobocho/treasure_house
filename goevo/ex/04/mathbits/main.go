// 슬라이드 p4-v19-mathbits — math/bits, Go 1.9
package main

import (
	"fmt"
	"math/bits"
)

func main() {
	var x uint8 = 0xb6
	fmt.Printf("x              %08b\n", x)
	fmt.Printf("OnesCount8     %d\n", bits.OnesCount8(x))
	fmt.Printf("LeadingZeros8  %d\n", bits.LeadingZeros8(x>>3))
	fmt.Printf("TrailingZeros8 %d\n", bits.TrailingZeros8(x))
	fmt.Printf("Reverse8       %08b\n", bits.Reverse8(x))
	fmt.Printf("RotateLeft8    %08b\n", bits.RotateLeft8(x, 2))
	fmt.Printf("Len64(1000)    %d\n", bits.Len64(1000))
}
