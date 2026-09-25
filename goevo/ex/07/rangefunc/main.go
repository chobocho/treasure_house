// 슬라이드 p7-v123-rangefunc — 함수에 대한 range, Go 1.23
package main

import "fmt"

// Three iterator shapes the range clause accepts.
func times(n int) func(func() bool) {
	return func(yield func() bool) {
		for range n {
			if !yield() {
				return
			}
		}
	}
}

func evens(max int) func(func(int) bool) {
	return func(yield func(int) bool) {
		for i := 0; i <= max; i += 2 {
			if !yield(i) {
				return // the loop body said break
			}
		}
	}
}

func pairs(m []string) func(func(int, string) bool) {
	return func(yield func(int, string) bool) {
		for i, s := range m {
			if !yield(i, s) {
				return
			}
		}
	}
}

func main() {
	for range times(2) {
		fmt.Print("tick ")
	}
	for n := range evens(100) {
		if n > 6 {
			break
		}
		fmt.Print(n, " ")
	}
	for i, s := range pairs([]string{"x", "y"}) {
		fmt.Print(i, "=", s, " ")
	}
	fmt.Println()
}
