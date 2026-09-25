// 슬라이드 p6-v118-whygen — 요소 타입을 빼낸 Reverse 하나, Go 1.18
package main

import "fmt"

// Reverse reverses s in place, whatever its element type is.
func Reverse[E any](s []E) {
	first, last := 0, len(s)-1
	for first < last {
		s[first], s[last] = s[last], s[first]
		first++
		last--
	}
}

func main() {
	ints := []int{1, 2, 3, 4}
	words := []string{"go", "1.18", "generics"}
	Reverse(ints)
	Reverse(words)
	fmt.Println(ints, words)
}
