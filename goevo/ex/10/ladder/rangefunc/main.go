// 슬라이드 p10-ladder-4 — 함수에 대한 range(이터레이터), Go 1.23
package main

import "fmt"

func count(n int) func(func(int) bool) {
	return func(yield func(int) bool) {
		for i := 0; i < n; i++ {
			if !yield(i) {
				return
			}
		}
	}
}

func main() {
	for i := range count(3) {
		fmt.Print(i)
	}
	fmt.Println()
}
