// 슬라이드 p5-v116-embed — 파일 하나를 string 과 []byte 로, Go 1.16
package main

import (
	_ "embed" // needed for //go:embed into string or []byte
	"fmt"
	"strings"
)

//go:embed hello.txt
var hello string

//go:embed version.txt
var version []byte

func main() {
	fmt.Print(hello)
	fmt.Println("version:", strings.TrimSpace(string(version)))
	fmt.Println("bytes:", len(hello))
}
