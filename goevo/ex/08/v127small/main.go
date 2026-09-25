// 슬라이드 p8-v127-small — CutLast·Int.Divide·URL.Clone, Go 1.27
package main

import (
	"bytes"
	"fmt"
	"math/big"
	"net/url"
	"strings"
)

func main() {
	// strings/bytes.CutLast: split around the last separator.
	dir, file, ok := strings.CutLast("go/src/net/http", "/")
	fmt.Println(dir, file, ok)
	_, ext, _ := bytes.CutLast([]byte("deck.tar.gz"), []byte("."))
	fmt.Println(string(ext))

	// math/big: quotient and remainder with a rounding mode.
	x, y := big.NewInt(-7), big.NewInt(2)
	for _, m := range []big.RoundingMode{big.Trunc, big.Floor,
		big.Ceil} {
		q, r := new(big.Int).Divide(x, y, new(big.Int), m)
		fmt.Printf("%v: q=%v r=%v  ", m, q, r)
	}
	fmt.Println()

	// net/url: a deep copy.
	u, _ := url.Parse("https://go.dev/doc?v=1.27")
	c := u.Clone()
	c.Path = "/blog"
	fmt.Println(u, c)
}
