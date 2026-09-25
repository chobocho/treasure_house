// 슬라이드 p7-v123-small — Repeat·Map.Clear·And/Or, Go 1.23
package main

import (
	"fmt"
	"slices"
	"sync"
	"sync/atomic"
)

func main() {
	fmt.Println(slices.Repeat([]string{"ab", "c"}, 3))

	var m sync.Map
	m.Store("a", 1)
	m.Store("b", 2)
	m.Clear() // like the clear built-in
	_, ok := m.Load("a")
	fmt.Println(ok)

	var flags atomic.Uint32
	flags.Store(0b0101)
	old := flags.Or(0b0010) // returns the old value
	fmt.Printf("%04b -> %04b\n", old, flags.Load())
	old = flags.And(0b0110)
	fmt.Printf("%04b -> %04b\n", old, flags.Load())
}
