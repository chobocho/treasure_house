// 슬라이드 p6-v120-unsafe — unsafe.String·StringData·SliceData, Go 1.20
package main

import (
	"fmt"
	"unsafe"
)

func main() {
	b := []byte("hello, 1.20")

	// Build a string that shares b's bytes: no copy.
	s := unsafe.String(unsafe.SliceData(b), len(b))
	fmt.Println(s)

	// Take it apart again: a pointer to the first byte and a length.
	p := unsafe.StringData(s)
	back := unsafe.Slice(p, len(s)) // unsafe.Slice is from 1.17
	fmt.Println(&back[0] == &b[0], len(back))

	// The contract: b must not change while s is in use.
}
