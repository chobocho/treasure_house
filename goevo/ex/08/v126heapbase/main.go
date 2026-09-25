// 슬라이드 p8-v126-heapbase — 힙 시작 주소 무작위화, Go 1.26
package main

import (
	"fmt"
	"runtime"
	"unsafe"
)

var sink *[64]byte

func main() {
	sink = new([64]byte) // escapes: lives on the heap
	addr := uint64(uintptr(unsafe.Pointer(sink)))

	// Without randomization the runtime tries fixed address hints
	// (runtime/malloc.go): 0x00c0<<32 on most 64-bit systems,
	// 0x0040<<32 on arm64. We never print the address itself, only
	// whether the heap sits in the first 4 GiB above that hint.
	hint := uint64(0x00c0) << 32
	if runtime.GOARCH == "arm64" {
		hint = uint64(0x0040) << 32
	}
	fmt.Printf("%s: heap at the fixed hint %#x: %v\n",
		runtime.GOARCH, hint, addr>>32 == hint>>32)
}
