// 슬라이드 p7-v124-alias — 제네릭 타입 별칭, Go 1.24
package main

import "fmt"

// A generic alias: Set[K] is not a new type, just another name.
type Set[K comparable] = map[K]struct{}

// Aliases may also narrow type parameters of a generic type.
type Pair[A, B any] struct {
	First  A
	Second B
}
type StrPair[V any] = Pair[string, V]

func keys(m map[string]struct{}) int { return len(m) }

func main() {
	s := Set[string]{"go": {}, "rust": {}}
	fmt.Println(keys(s)) // identical type: no conversion needed
	p := StrPair[int]{"age", 30}
	fmt.Printf("%v %T\n", p, p)
}
