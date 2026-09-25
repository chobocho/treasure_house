// 슬라이드 p10-ladder-2 — 타입 매개변수, Go 1.18
package main

import "fmt"

func Map[T, U any](xs []T, f func(T) U) []U {
	var out []U
	for _, x := range xs {
		out = append(out, f(x))
	}
	return out
}

func main() {
	toString := func(i int) string { return fmt.Sprint(i) }
	fmt.Println(Map([]int{1, 2}, toString))
}
