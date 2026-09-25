// 슬라이드 p8-v126-stackslice — append 슬라이스의 스택 할당, Go 1.26
package main

import (
	"fmt"
	"testing"
)

var sink []int

//go:noinline
func use(s []int) int { return len(s) } // does not keep s

// local's slice never escapes: the first backing store can be a
// small buffer on the stack.
//
//go:noinline
func local(n int) int {
	var s []int
	for i := range n {
		s = append(s, i)
	}
	return use(s)
}

// extract returns its slice, so the result must end up on the heap.
//
//go:noinline
func extract(n int) []int {
	var s []int
	for i := range n {
		s = append(s, i)
	}
	return s
}

func main() {
	for _, n := range []int{1, 3, 4, 5, 8, 16} {
		a := testing.AllocsPerRun(100, func() { _ = local(n) })
		b := testing.AllocsPerRun(100, func() { sink = extract(n) })
		fmt.Printf("n=%-2d  local: %v allocs   extract: %v allocs\n",
			n, a, b)
	}
}
