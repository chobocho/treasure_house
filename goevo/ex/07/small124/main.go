// 슬라이드 p7-v124-small — rand.Text·Comparable·Appender, Go 1.24
package main

import (
	"crypto/rand"
	"fmt"
	"hash/maphash"
	"time"
)

type Key struct {
	User string
	ID   int
}

func main() {
	tok := rand.Text() // base32, at least 128 bits of randomness
	fmt.Println(len(tok), "chars")

	seed := maphash.MakeSeed()
	h1 := maphash.Comparable(seed, Key{"ana", 1})
	h2 := maphash.Comparable(seed, Key{"ana", 1})
	fmt.Println("same key, same hash:", h1 == h2)

	buf := []byte("at=")
	t := time.Date(2025, 2, 11, 0, 0, 0, 0, time.UTC)
	buf, _ = t.AppendText(buf) // encoding.TextAppender
	fmt.Println(string(buf))
}
