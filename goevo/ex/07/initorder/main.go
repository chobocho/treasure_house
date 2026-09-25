// 슬라이드 p7-v121-initorder — 패키지 초기화 순서의 명세, Go 1.21
package main

import (
	"fmt"

	_ "ex/07/initorder/zeta" // imported first here
)

func main() { fmt.Println("main") }
