// 슬라이드 p4-v15-bigfloat — math/big.Float, Go 1.5
package main

import (
	"fmt"
	"math/big"
)

func main() {
	// 1/3 at three precisions (mantissa bits).
	for _, prec := range []uint{24, 53, 200} {
		x := new(big.Float).SetPrec(prec).SetInt64(1)
		x.Quo(x, big.NewFloat(3))
		fmt.Printf("%3d bits: %s\n", prec, x.Text('g', 40))
	}
	// At 53 bits the result is exactly the float64 result.
	third := new(big.Float).SetPrec(53)
	third.Quo(big.NewFloat(1), big.NewFloat(3))
	f, _ := third.Float64()
	fmt.Println("53 bits == float64:", f == 1.0/3)
}
