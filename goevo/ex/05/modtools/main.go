// 슬라이드 p5-v111-modcmds — 의존 모듈 하나, Go 1.11
package main

import (
	"fmt"

	"example.com/lib"
)

func main() {
	fmt.Println(lib.Greeting())
}
