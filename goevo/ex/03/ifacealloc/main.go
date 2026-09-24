// 슬라이드 p3-v14-runtime — 인터페이스 값은 늘 포인터를 담는다, Go 1.4
package main

import (
	"fmt"
	"testing"
)

var sink interface{}

func main() {
	big, small := 1000, 7
	p := &big

	fmt.Println("pointer:  ", testing.AllocsPerRun(100, func() {
		sink = p // a pointer fits the interface's data word
	}))
	fmt.Println("int 1000: ", testing.AllocsPerRun(100, func() {
		sink = big // the int is boxed on the heap
	}))
	fmt.Println("int 7:    ", testing.AllocsPerRun(100, func() {
		sink = small // runtime keeps a static table for 0..255
	}))
	fmt.Println("string:   ", testing.AllocsPerRun(100, func() {
		sink = "go" // constant data: no allocation
	}))
}
