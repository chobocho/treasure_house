// 슬라이드 p5-v117-slice2arr — 슬라이스에서 배열 포인터로, Go 1.17
package main

import "fmt"

func main() {
	s := []byte{'G', 'o', '1', '.', '1', '7'}

	p := (*[2]byte)(s) // shares s's backing array
	p[0] = 'g'
	fmt.Println(string(s), len(p), &p[1] == &s[1])

	// Before: copy into an array, or go through unsafe.
	var a [2]byte
	copy(a[:], s)
	fmt.Println(string(a[:]))
}
