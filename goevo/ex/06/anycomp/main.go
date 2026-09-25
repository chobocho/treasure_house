// 슬라이드 p6-v118-anycomp — 미리 선언된 any 와 comparable, Go 1.18
package main

import "fmt"

// Index needs ==, so T must be comparable, not just any.
func Index[T comparable](s []T, x T) int {
	for i, v := range s {
		if v == x {
			return i
		}
	}
	return -1
}

type point struct{ X, Y int }

func main() {
	// any is an alias: the two types are identical.
	var a any = 1
	var e interface{} = a
	fmt.Println(a == e)

	fmt.Println(Index([]string{"a", "b"}, "b"))
	fmt.Println(Index([]point{{1, 2}, {3, 4}}, point{3, 4}))
}
