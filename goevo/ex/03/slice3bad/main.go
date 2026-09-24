// 슬라이드 p3-v12-slice3 — 셋째·둘째 인덱스는 생략 불가, Go 1.2
package main

import "fmt"

func main() {
	a := []int{0, 1, 2, 3, 4}
	fmt.Println(a[:2:4]) // ok: a missing first index is 0
	fmt.Println(a[1:2:]) // the third index is required
	fmt.Println(a[1::4]) // so is the second
}
