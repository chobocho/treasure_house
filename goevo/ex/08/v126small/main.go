// 슬라이드 p8-v126-small — Peek·Compare·sha3 의 0 값, Go 1.26
package main

import (
	"bytes"
	"crypto/sha3"
	"fmt"
	"net/netip"
	"slices"
)

func main() {
	// bytes.Buffer.Peek: look ahead without consuming.
	var buf bytes.Buffer
	buf.WriteString("GET /index.html")
	head, err := buf.Peek(3)
	fmt.Printf("peek %q %v, still %d bytes\n", head, err, buf.Len())
	_, err = buf.Peek(99)
	fmt.Println("peek 99:", err)

	// netip.Prefix.Compare: prefixes are now sortable.
	ps := []netip.Prefix{
		netip.MustParsePrefix("10.1.0.0/16"),
		netip.MustParsePrefix("10.0.0.0/8"),
		netip.MustParsePrefix("10.1.0.0/24"),
	}
	slices.SortFunc(ps, netip.Prefix.Compare)
	fmt.Println(ps)

	// The zero value of sha3.SHA3 is a usable SHA3-256.
	var h sha3.SHA3
	h.Write([]byte("go"))
	fmt.Printf("sha3-256 %x… (%d bytes)\n", h.Sum(nil)[:4], h.Size())
	fmt.Println(sha3.Sum256([]byte("go")) == [32]byte(h.Sum(nil)))
}
