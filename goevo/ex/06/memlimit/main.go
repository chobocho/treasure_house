// 슬라이드 p6-v119-memlimit — 부드러운 메모리 상한 GOMEMLIMIT, Go 1.19
package main

import (
	"fmt"
	"math"
	"runtime/debug"
)

func main() {
	// A negative value only reads the current limit.
	limit := debug.SetMemoryLimit(-1)
	if limit == math.MaxInt64 {
		fmt.Println("limit: none (math.MaxInt64)")
	} else {
		fmt.Printf("limit: %d bytes = %d MiB\n", limit, limit>>20)
	}
	fmt.Println("GOGC:", debug.SetGCPercent(-1))
}
