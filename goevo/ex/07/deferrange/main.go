// 슬라이드 p7-v123-defer — range-over-func 몸체의 defer, Go 1.23
package main

import (
	"fmt"
	"slices"
)

func main() {
	fmt.Println("start")
	for v := range slices.Values([]int{1, 2}) {
		// Runs when main returns, not when yield returns:
		// the body behaves like an ordinary loop body.
		defer fmt.Println("deferred", v)
	}
	fmt.Println("end of main")
}
