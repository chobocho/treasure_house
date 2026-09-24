// 슬라이드 p3-v12-small — sort.Stable·Sum256·SwapInt32, Go 1.2
package main

import (
	"crypto/sha256"
	"fmt"
	"sort"
	"sync/atomic"
)

type byLen []string

func (s byLen) Len() int           { return len(s) }
func (s byLen) Less(i, j int) bool { return len(s[i]) < len(s[j]) }
func (s byLen) Swap(i, j int)      { s[i], s[j] = s[j], s[i] }

func main() {
	// equal-length words keep their input order
	words := byLen{"gc", "go", "vet", "fmt", "cgo", "godoc"}
	sort.Stable(words)
	fmt.Println(words)

	// one call, no hash.Hash value; the result is an array
	sum := sha256.Sum256([]byte("go1.2"))
	fmt.Printf("%T %x\n", sum, sum[:4])

	var state int32 = 1
	old := atomic.SwapInt32(&state, 2)
	fmt.Println("old:", old, "new:", state)
}
