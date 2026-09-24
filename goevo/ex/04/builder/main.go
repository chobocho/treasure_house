// 슬라이드 p4-v110-builder — strings.Builder, Go 1.10
package main

import (
	"fmt"
	"strings"
)

func join(parts []string) string {
	var b strings.Builder // zero value is ready to use
	for i, p := range parts {
		if i > 0 {
			b.WriteByte(',')
		}
		b.WriteString(p)
	}
	return b.String() // no copy of the bytes
}

func main() {
	fmt.Println(join([]string{"a", "b", "c"}))
}
