// 슬라이드 p5-v116-embedrules — 넣을 수 없는 것들, Go 1.16
package main

import (
	_ "embed"
	"fmt"
)

//go:embed ../README.md
var parent string

func main() {
	fmt.Println(parent)
}
