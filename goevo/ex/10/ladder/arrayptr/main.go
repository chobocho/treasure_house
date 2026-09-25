// 슬라이드 p10-ladder-2 — 슬라이스를 배열 포인터로, Go 1.17
package main

import "fmt"

func main() {
	s := []int{1, 2, 3}
	p := (*[2]int)(s)
	fmt.Println(*p)
}
