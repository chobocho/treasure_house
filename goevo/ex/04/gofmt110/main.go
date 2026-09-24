// 슬라이드 p4-v110-gofmt — gofmt 가 바꾼 두 모양, Go 1.10
package main

import (
	"fmt"
	"strconv"
)

type num int

func (n num) String() string { return "#" + strconv.Itoa(int(n)) }

func main() {
	x := []int{0, 1, 2, 3, 4, 5}
	i, j, k := 0, 3, 4
	y := x[i+1 : j : k] // 1.9 printed x[i+1 : j:k]
	fmt.Println(y, len(y), cap(y))

	var v interface{} = num(7)
	// A one-line interface literal now stays on one line.
	if s, ok := v.(interface{ String() string }); ok {
		fmt.Println(s.String())
	}
}
