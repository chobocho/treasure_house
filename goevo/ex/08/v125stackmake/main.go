// 슬라이드 p8-v125-stackmake — 크기가 변수인 make 도 스택에, Go 1.25
package main

import (
	"fmt"
	"testing"
)

// checksum makes a buffer whose size is known only at run time.
// The buffer never escapes, so the compiler may keep it on the
// stack when it is small enough.
//
//go:noinline
func checksum(n int) byte {
	buf := make([]byte, n)
	for i := range buf {
		buf[i] = byte(i * 7)
	}
	var s byte
	for _, b := range buf {
		s ^= b
	}
	return s
}

func main() {
	for _, n := range []int{8, 32, 33, 1024} {
		allocs := testing.AllocsPerRun(100, func() { checksum(n) })
		fmt.Printf("make([]byte, %4d): %.0f allocs/op\n", n, allocs)
	}
}
