// 슬라이드 p7-v123-adapters — 반복자 어댑터 Filter·Map, Go 1.23
package main

import (
	"fmt"
	"iter"
	"slices"
	"strings"
)

func Filter[V any](seq iter.Seq[V], keep func(V) bool) iter.Seq[V] {
	return func(yield func(V) bool) {
		for v := range seq {
			if keep(v) && !yield(v) {
				return
			}
		}
	}
}

func Map[V, R any](seq iter.Seq[V], f func(V) R) iter.Seq[R] {
	return func(yield func(R) bool) {
		for v := range seq {
			if !yield(f(v)) {
				return
			}
		}
	}
}

func main() {
	words := slices.Values([]string{"go", "iter", "yield", "pull"})
	long := Filter(words, func(w string) bool { return len(w) > 3 })
	upper := Map(long, strings.ToUpper)
	fmt.Println(slices.Collect(upper)) // nothing runs until here
}
