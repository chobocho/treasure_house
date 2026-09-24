// 슬라이드 p5-v117-unsafe — unsafe.Add 와 unsafe.Slice, Go 1.17
package main

import (
	"fmt"
	"unsafe"
)

func main() {
	arr := [4]int32{10, 20, 30, 40}
	p := unsafe.Pointer(&arr[0])

	// Before: unsafe.Pointer(uintptr(p) + 8), easy to get wrong.
	third := (*int32)(unsafe.Add(p, 2*unsafe.Sizeof(arr[0])))
	fmt.Println(*third)

	// A slice header built from a pointer and a length.
	s := unsafe.Slice(&arr[1], 3)
	fmt.Println(s, len(s), cap(s))
}
