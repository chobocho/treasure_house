// 슬라이드 p4-v15-godoc — go doc 과 strings.Compare, Go 1.5
package main

import (
	"fmt"
	"strings"
)

func main() {
	// strings.Compare (1.5) exists for symmetry with bytes.Compare.
	fmt.Println(strings.Compare("a", "b"), "a" < "b")
}
