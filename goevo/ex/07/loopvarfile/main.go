// 슬라이드 p7-v122-loopvarfile — go 1.21 모듈의 옛 의미, Go 1.22
package main

import "fmt"

func perLoop() []int {
	var ps []*int
	for i := 0; i < 3; i++ {
		ps = append(ps, &i)
	}
	return []int{*ps[0], *ps[1], *ps[2]}
}

func main() {
	fmt.Println("main.go  (go 1.21):", perLoop())
	fmt.Println("new.go   (go1.22): ", perIteration())
}
