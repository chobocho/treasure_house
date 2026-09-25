// 슬라이드 p6-v118-shape — 같은 모양은 코드 한 벌, Go 1.18
package main

import "fmt"

type Celsius float64

//go:noinline
func Largest[T int | float64 | Celsius | string](xs []T) T {
	m := xs[0]
	for _, x := range xs[1:] {
		if x > m {
			m = x
		}
	}
	return m
}

func main() {
	fmt.Println(Largest([]int{3, 9, 2}))
	fmt.Println(Largest([]float64{1.5, 0.5}))
	fmt.Println(Largest([]Celsius{20, 36.5}))
	fmt.Println(Largest([]string{"go", "zig"}))
}
