// 슬라이드 p4-v17-ssa — SSA 와 경계 검사 제거, Go 1.7
package main

import "fmt"

func sum4(s []int) int {
	return s[0] + s[1] + s[2] + s[3] // a check per index
}

func sum4hint(s []int) int {
	_ = s[3] // one check up front proves the other three
	return s[0] + s[1] + s[2] + s[3]
}

func main() {
	s := []int{1, 2, 3, 4}
	fmt.Println(sum4(s), sum4hint(s))
}
