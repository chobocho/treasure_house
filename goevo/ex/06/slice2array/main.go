// 슬라이드 p6-v120-slicearray — 슬라이스를 배열로 바로 변환, Go 1.20
package main

import "fmt"

func main() {
	s := []byte{1, 2, 3, 4, 5}

	a := [4]byte(s)          // 1.20: a copy of the first 4 bytes
	p := (*[4]byte)(s)       // 1.17: a pointer into s itself
	b := *(*[4]byte)(s)      // the pre-1.20 spelling of a
	s[0] = 9                 // change the slice afterwards
	fmt.Println(a, *p, b, s) // only p sees the 9

	defer func() { fmt.Println("recovered:", recover()) }()
	_ = [8]byte(s) // len(s) < 8: panics at run time
}
