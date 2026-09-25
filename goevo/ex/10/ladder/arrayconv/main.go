// 슬라이드 p10-ladder-3 — 슬라이스를 배열 값으로, Go 1.20
package main

import "fmt"

func main() {
	s := []int{1, 2, 3}
	fmt.Println([2]int(s))
}
