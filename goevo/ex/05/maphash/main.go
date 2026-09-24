// 슬라이드 p5-v114-maphash — 해시 테이블용 바이트열 해시, Go 1.14
package main

import (
	"fmt"
	"hash/maphash"
)

func main() {
	seed := maphash.MakeSeed() // random per process

	var h maphash.Hash
	h.SetSeed(seed)
	h.WriteString("gopher")
	a := h.Sum64()

	h.Reset() // keeps the seed
	h.WriteString("gopher")
	b := h.Sum64()

	var other maphash.Hash // a fresh Hash picks its own seed
	other.WriteString("gopher")

	fmt.Println("same seed, same input:", a == b)
	fmt.Println("other seed:           ", a == other.Sum64())
	fmt.Println("buckets(8):", a%8 == b%8)
}
