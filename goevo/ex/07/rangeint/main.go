// 슬라이드 p7-v122-rangeint — 정수 range 의 타입과 경계, Go 1.22
package main

import (
	"fmt"
	"time"
)

type Weekday int

func main() {
	var n int64 = 3
	for i := range n {
		fmt.Printf("%T %d  ", i, i) // i has the type of n
	}
	fmt.Println()

	for d := range Weekday(2) {
		fmt.Printf("%T(%d) ", d, d)
	}
	fmt.Println()

	for range -5 { // zero or negative: no iterations
		fmt.Println("never")
	}
	for i := range time.Duration(2) {
		fmt.Println(i) // a Duration prints as 0s, 1ns
	}
}
