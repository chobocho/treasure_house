// 슬라이드 p6-v119-gcoff — GOGC=off 와 GOMEMLIMIT, Go 1.19
package main

import (
	"fmt"
	"runtime"
)

var sink []byte

func main() {
	var before, after runtime.MemStats
	runtime.ReadMemStats(&before)
	// 96 MiB of short-lived garbage, 1 MiB at a time.
	for i := 0; i < 96; i++ {
		sink = make([]byte, 1<<20)
	}
	runtime.ReadMemStats(&after)
	ran := after.NumGC > before.NumGC
	fmt.Println("GC ran:", ran)
	fmt.Println("heap under 48 MiB:", after.HeapSys < 48<<20)
}
