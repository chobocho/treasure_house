// 슬라이드 p4-v15-gomaxprocs — GOMAXPROCS 기본값, Go 1.5
package main

import (
	"fmt"
	"runtime"
)

func main() {
	n := runtime.GOMAXPROCS(0) // 0 only queries the setting
	fmt.Println("GOMAXPROCS == NumCPU:", n == runtime.NumCPU())
	fmt.Println("more than one P:", n > 1)
}
