// 슬라이드 p8-v126-selfref — 자기를 가리키는 제약, Go 1.26
package main

import "fmt"

// Ordered may only be instantiated with a type that compares
// against its own kind: the constraint names Ordered itself.
type Ordered[T Ordered[T]] interface {
	Less(T) bool
}

func Max[T Ordered[T]](xs ...T) T {
	m := xs[0]
	for _, x := range xs[1:] {
		if m.Less(x) {
			m = x
		}
	}
	return m
}

type Version struct{ Major, Minor int }

func (v Version) Less(w Version) bool {
	return v.Major < w.Major ||
		v.Major == w.Major && v.Minor < w.Minor
}

type Word string

func (a Word) Less(b Word) bool { return len(a) < len(b) }

func main() {
	fmt.Println(Max(Version{1, 26}, Version{1, 9}, Version{1, 18}))
	fmt.Println(Max[Word]("go", "gopher", "gc"))
}
