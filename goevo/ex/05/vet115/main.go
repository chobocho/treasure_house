// 슬라이드 p5-v115-vet — string(int) 와 불가능한 단언, Go 1.15
package main

import (
	"fmt"
	"io"
	"strings"
)

// Stopper's Close has no result; io.Closer's returns error.
type Stopper interface{ Close() }

func main() {
	n := 9786
	fmt.Println(string(n)) // a rune, not "9786"

	var c io.Closer = io.NopCloser(strings.NewReader(""))
	_, ok := c.(Stopper) // can never succeed
	fmt.Println(ok)
}
