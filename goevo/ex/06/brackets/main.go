// 슬라이드 p6-v118-brackets — 왜 꺾쇠가 아니라 대괄호인가, Go 1.18
package main

import "fmt"

func main() {
	w, x, y, z := 1, 2, 3, 4
	var a, b bool
	// With <> for type arguments this line would have two readings:
	// two comparisons, or a generic call w<x, y>(z).
	a, b = w < x, y > (z)
	fmt.Println(a, b)
}
