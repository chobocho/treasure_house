// 슬라이드 p6-v118-inference — 제약 타입 추론: S ~[]E, Go 1.18
package main

import (
	"fmt"
	"strings"
)

type Integer interface{ ~int | ~int32 | ~int64 }

// Scale returns a copy of s with each element multiplied by c.
// S keeps the caller's slice type; E is inferred from S.
func Scale[S ~[]E, E Integer](s S, c E) S {
	r := make(S, len(s))
	for i, v := range s {
		r[i] = v * c
	}
	return r
}

// Path is a slice with a method of its own.
type Path []int32

func (p Path) String() string {
	parts := make([]string, len(p))
	for i, v := range p {
		parts[i] = fmt.Sprint(v)
	}
	return strings.Join(parts, "→")
}

func main() {
	p := Path{1, 2, 3}
	r := Scale(p, 10) // no type arguments: S=Path, E=int32
	fmt.Println(r.String())
	fmt.Printf("%T\n", r)
}
