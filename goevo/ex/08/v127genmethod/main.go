// 슬라이드 p8-v127-genmethod — 제네릭 메서드, Go 1.27
package main

import (
	"fmt"
	"strconv"
)

type List[E any] struct{ elems []E }

func NewList[E any](elems ...E) List[E] { return List[E]{elems} }

// Map declares its own type parameter R — new in Go 1.27.
func (l List[E]) Map[R any](f func(E) R) List[R] {
	out := make([]R, len(l.elems))
	for i, e := range l.elems {
		out[i] = f(e)
	}
	return List[R]{out}
}

func add(n int) func(int) int {
	return func(x int) int { return x + n }
}

func main() {
	l := NewList(0, 2, 4)
	fmt.Println(l.Map(add(2)).Map(strconv.Itoa).elems)

	// A method expression turns it back into a function.
	f := List[int].Map[string]
	fmt.Printf("%q\n", f(l, strconv.Itoa).elems)
}
