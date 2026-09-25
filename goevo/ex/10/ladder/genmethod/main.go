// 슬라이드 p10-ladder-5 — 제네릭 메서드, Go 1.27
package main

import "fmt"

type Box struct{ v int }

func (b Box) Apply[T any](f func(int) T) T { return f(b.v) }

func main() {
	double := func(i int) string { return fmt.Sprint(i * 2) }
	fmt.Println(Box{21}.Apply(double))
}
