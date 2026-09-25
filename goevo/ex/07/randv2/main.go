// 슬라이드 p7-v122-randv2 — math/rand/v2, Go 1.22
package main

import (
	"fmt"
	"math/rand/v2"
	"time"
)

func main() {
	// Seeded sources give a fixed sequence (only for tests and demos).
	r := rand.New(rand.NewPCG(1, 2))
	fmt.Println(r.IntN(100), r.IntN(100), r.Uint64N(1000))

	var seed [32]byte
	c := rand.New(rand.NewChaCha8(seed))
	fmt.Println(c.IntN(100), c.Float64() < 1)

	// N is generic: any integer type, e.g. a Duration.
	d := rand.N(5 * time.Minute)
	fmt.Println(d >= 0 && d < 5*time.Minute)

	// Top-level functions are always randomly seeded: no Seed at all.
	fmt.Println(rand.IntN(6) < 6)
}
