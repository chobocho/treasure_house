// 슬라이드 p6-v118-inference — []E 를 돌려주면, Go 1.18
package main

import "fmt"

type Integer interface{ ~int | ~int32 | ~int64 }

func Scale[E Integer](s []E, c E) []E {
	r := make([]E, len(s))
	for i, v := range s {
		r[i] = v * c
	}
	return r
}

type Path []int32

func (p Path) String() string { return fmt.Sprint([]int32(p)) }

func main() {
	r := Scale(Path{1, 2, 3}, 10)
	fmt.Println(r.String())
}
