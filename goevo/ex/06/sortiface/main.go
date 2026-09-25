// 슬라이드 p6-v118-before — 인터페이스로 흉내 낸 Reverse, Go 1.18
package main

import "fmt"

// Swapper is what an interface-based Reverse needs from a slice.
type Swapper interface {
	Len() int
	Swap(i, j int)
}

func Reverse(s Swapper) {
	for i, j := 0, s.Len()-1; i < j; i, j = i+1, j-1 {
		s.Swap(i, j)
	}
}

// Every slice type has to bring the same two methods.
type Ints []int

func (s Ints) Len() int      { return len(s) }
func (s Ints) Swap(i, j int) { s[i], s[j] = s[j], s[i] }

type Words []string

func (s Words) Len() int      { return len(s) }
func (s Words) Swap(i, j int) { s[i], s[j] = s[j], s[i] }

func main() {
	ints := []int{1, 2, 3, 4}
	words := []string{"go", "1.17", "interfaces"}
	Reverse(Ints(ints))
	Reverse(Words(words))
	fmt.Println(ints, words)
}
