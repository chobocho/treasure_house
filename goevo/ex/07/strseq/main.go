// 슬라이드 p7-v124-strseq — strings 의 반복자 함수, Go 1.24
package main

import (
	"fmt"
	"strings"
)

const text = "alpha beta\n  gamma\ndelta"

func main() {
	for line := range strings.Lines(text) {
		fmt.Printf("%q ", line) // keeps the newline
	}
	fmt.Println()
	for f := range strings.FieldsSeq(text) {
		fmt.Print("[", f, "]")
	}
	fmt.Println()
	for part := range strings.SplitSeq("a,b,,c", ",") {
		fmt.Printf("%q ", part) // no []string is allocated
	}
	fmt.Println()
}
