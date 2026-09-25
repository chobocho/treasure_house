// 슬라이드 p6-v120-comparable — any 도 comparable 만족, Go 1.20
package main

import "fmt"

// Set is a user-defined generic set: its keys must be comparable.
type Set[K comparable] map[K]struct{}

func (s Set[K]) Add(k K) { s[k] = struct{}{} }

func main() {
	s := Set[any]{} // any: comparable, but not strictly comparable
	s.Add(1)
	s.Add("one")
	fmt.Println(len(s))

	defer func() { fmt.Println("panic:", recover()) }()
	s.Add([]int{1}) // a slice inside the interface: panics
}
