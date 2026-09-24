// 슬라이드 p3-v11-methodvalue — 메서드 값과 메서드 식, Go 1.1
package main

import (
	"fmt"
	"strings"
)

type Counter struct{ n int }

func (c *Counter) Add(k int) { c.n += k }
func (c Counter) Get() int   { return c.n }

func apply(f func(string) string, xs []string) []string {
	out := make([]string, 0, len(xs))
	for _, x := range xs {
		out = append(out, f(x))
	}
	return out
}

func main() {
	c := &Counter{}

	add := c.Add // method value: receiver c is bound here
	add(2)
	add(3)
	fmt.Println("after add:", c.n)

	addTo := (*Counter).Add // method expression: receiver is arg 1
	addTo(c, 10)
	fmt.Println("after addTo:", c.n)

	r := strings.NewReplacer("a", "4", "o", "0")
	fmt.Println(apply(r.Replace, []string{"go", "java"}))

	// a value receiver is copied when the method value is made
	get := c.Get
	c.Add(100)
	fmt.Println("get():", get(), "c.Get():", c.Get())
}
