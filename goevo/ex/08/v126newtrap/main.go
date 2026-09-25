// 슬라이드 p8-v126-newtrap — new(x) 는 x 를 가리키지 않는다, Go 1.26
package main

import "fmt"

var calls int

func next() int {
	calls++
	return calls * 10
}

func main() {
	x := 1
	p := &x     // points at x itself
	q := new(x) // a new variable holding a copy of x
	*p = 2
	*q = 3
	fmt.Println("x =", x, "*p =", *p, "*q =", *q)

	// new(x) twice gives two different variables.
	r, s := new(x), new(x)
	fmt.Println("r == s:", r == s)

	// The operand is evaluated exactly once, when new runs.
	t := new(next())
	fmt.Println("*t =", *t, "calls =", calls)
}
