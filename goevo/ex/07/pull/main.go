// 슬라이드 p7-v123-pull — iter.Pull 로 두 시퀀스를 나란히, Go 1.23
package main

import (
	"fmt"
	"iter"
	"slices"
)

// Zip pairs up two push iterators by turning them into pull iterators.
func Zip[A, B any](as iter.Seq[A], bs iter.Seq[B]) iter.Seq2[A, B] {
	return func(yield func(A, B) bool) {
		nextA, stopA := iter.Pull(as)
		defer stopA()
		nextB, stopB := iter.Pull(bs)
		defer stopB()
		for {
			a, ok1 := nextA()
			b, ok2 := nextB()
			if !ok1 || !ok2 || !yield(a, b) {
				return
			}
		}
	}
}

func main() {
	names := slices.Values([]string{"ana", "bo", "cy"})
	ages := slices.Values([]int{31, 25})
	for n, a := range Zip(names, ages) {
		fmt.Println(n, a)
	}
}
