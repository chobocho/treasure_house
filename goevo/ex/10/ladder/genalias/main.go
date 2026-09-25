// 슬라이드 p10-ladder-4 — 제네릭 타입 별칭, Go 1.24
package main

import "fmt"

type Set[T comparable] = map[T]struct{}

func main() {
	s := Set[string]{"go": {}}
	fmt.Println(len(s))
}
