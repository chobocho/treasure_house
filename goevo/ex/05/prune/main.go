// 슬라이드 p5-v117-prune — 주 모듈은 a 만 import 한다, Go 1.17
package main

import (
	"fmt"

	"example.com/a"
)

func main() {
	fmt.Println(a.Name())
}
