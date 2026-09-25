// 슬라이드 p6-v118-generictype — 제네릭 타입과 그 메서드, Go 1.18
package main

import "fmt"

// Stack stores values of T directly, not as interface values.
type Stack[T any] struct {
	items []T
}

// Methods name the type parameter again in the receiver.
func (s *Stack[T]) Push(v T) { s.items = append(s.items, v) }

func (s *Stack[T]) Pop() (T, bool) {
	var zero T
	if len(s.items) == 0 {
		return zero, false
	}
	v := s.items[len(s.items)-1]
	s.items = s.items[:len(s.items)-1]
	return v, true
}

// Pair has two type parameters.
type Pair[K comparable, V any] struct {
	Key K
	Val V
}

func main() {
	var s Stack[Pair[string, int]]
	s.Push(Pair[string, int]{"a", 1})
	s.Push(Pair[string, int]{"b", 2})
	top, _ := s.Pop()
	fmt.Printf("%+v %T\n", top, s)
	_, ok := new(Stack[float64]).Pop()
	fmt.Println(ok)
}
