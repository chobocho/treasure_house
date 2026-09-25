// 슬라이드 p7-v122-loopvar3 — 세 칸 for 문의 반복별 변수, Go 1.22
package main

import "fmt"

func main() {
	var ptrs []*int
	for i := 0; i < 3; i++ {
		ptrs = append(ptrs, &i)
	}
	fmt.Println(*ptrs[0], *ptrs[1], *ptrs[2], ptrs[0] == ptrs[1])

	// The body may still change i: the new variable of the next
	// iteration starts from the value at the end of this one.
	for i := 0; i < 10; i++ {
		fmt.Print(i, " ")
		i += 2
	}
	fmt.Println()
}
