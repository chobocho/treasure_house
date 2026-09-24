// 슬라이드 p3-v12-runtime — 스레드 수 상한과 스택 최대 크기, Go 1.2
package main

import (
	"fmt"
	"runtime/debug"
)

func main() {
	// each setter returns the previous value: read the defaults
	threads := debug.SetMaxThreads(20000)
	debug.SetMaxThreads(threads)
	fmt.Println("default max threads:", threads)

	stack := debug.SetMaxStack(64 << 20)
	debug.SetMaxStack(stack)
	fmt.Println("default max stack:  ", stack, "bytes")
}
