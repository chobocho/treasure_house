// 슬라이드 p4-v19-frames — 인라인된 프레임, Go 1.9
package main

import (
	"fmt"
	"runtime"
)

func where() []uintptr {
	pc := make([]uintptr, 8)
	return pc[:runtime.Callers(1, pc)]
}

func inner() []uintptr { return where() } // small: gets inlined

func main() {
	pcs := inner()
	fmt.Println("FuncForPC, one per PC:")
	for _, pc := range pcs {
		fmt.Println("  ", runtime.FuncForPC(pc).Name())
	}
	fmt.Println("CallersFrames:")
	frames := runtime.CallersFrames(pcs)
	for {
		f, more := frames.Next()
		fmt.Println("  ", f.Function)
		if !more {
			break
		}
	}
}
