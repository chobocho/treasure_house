// 슬라이드 p6-v118-cut — Index·SplitN 대신 strings.Cut, Go 1.18
package main

import (
	"fmt"
	"strings"
)

func main() {
	line := "Content-Type: text/plain; charset=utf-8"

	// Before: Index, then slice by hand, and remember the +len(sep).
	if i := strings.Index(line, ": "); i >= 0 {
		fmt.Printf("%q %q\n", line[:i], line[i+len(": "):])
	}

	// 1.18: one call, and found says whether sep was there.
	key, val, found := strings.Cut(line, ": ")
	fmt.Printf("%q %q %v\n", key, val, found)

	_, _, found = strings.Cut("no separator", ": ")
	fmt.Println(found)
}
