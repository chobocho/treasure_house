// 슬라이드 p4-v15-tricolor — GOGC 손잡이, Go 1.5
package main

import (
	"fmt"
	"runtime/debug"
)

func main() {
	// SetGCPercent returns the previous setting, which starts
	// out as the value of the GOGC environment variable.
	old := debug.SetGCPercent(100)
	fmt.Println("GOGC in effect:", old)
}
