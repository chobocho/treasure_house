// 슬라이드 p8-v127-small2 — Unicode 17·ComparableHasher, Go 1.27
package main

import (
	"fmt"
	"hash/maphash"
	"unicode"
)

type key struct{ x, y int }

func main() {
	fmt.Println("Unicode", unicode.Version)
	fmt.Println(unicode.Is(unicode.Garay, '\U00010D40')) // new script

	var h maphash.Hasher[key] = maphash.ComparableHasher[key]{}
	seed := maphash.MakeSeed()
	var a, b maphash.Hash
	a.SetSeed(seed)
	b.SetSeed(seed)
	h.Hash(&a, key{1, 2})
	h.Hash(&b, key{1, 2})
	fmt.Println(h.Equal(key{1, 2}, key{1, 2}), a.Sum64() == b.Sum64())
}
