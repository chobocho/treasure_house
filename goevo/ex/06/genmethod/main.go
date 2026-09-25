// 슬라이드 p6-v118-nomethod — 메서드의 타입 매개변수, Go 1.18
package main

import "fmt"

type Box struct{ v any }

// A method with its own type parameter list.
func (b Box) As[T any]() (T, bool) {
	t, ok := b.v.(T)
	return t, ok
}

func main() {
	n, ok := Box{42}.As[int]()
	fmt.Println(n, ok)
}
