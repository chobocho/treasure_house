// 슬라이드 p2-v10-complit — 포인터 원소의 타입 이름 생략, Go 1
package main

import "fmt"

type Date struct {
	month string
	day   int
}

func main() {
	// Pointers, type name elided; legal in Go 1.
	holiday := []*Date{
		{"Feb", 14},
		{"Nov", 11},
		{"Dec", 25},
	}
	for _, d := range holiday {
		fmt.Println(d.month, d.day)
	}
}
