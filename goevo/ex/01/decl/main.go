// 슬라이드 p1-decl — 이름이 타입보다 먼저, 1.27.1 에서의 동작
package main

import "fmt"

var count int

// A function that takes a func and returns one; read left to right.
func twice(f func(int) int) func(int) int {
	return func(x int) int { return f(f(x)) }
}

func main() {
	var p *[3]int = new([3]int)
	add1 := func(x int) int { return x + 1 }
	count = twice(add1)(40)
	fmt.Println(count, len(p))
}
