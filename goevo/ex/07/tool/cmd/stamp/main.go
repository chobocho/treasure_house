// 슬라이드 p7-v124-tool — 모듈이 기록한 도구, Go 1.24
package main

import (
	"fmt"
	"os"
)

func main() {
	fmt.Println("stamp: generating code for", os.Args[1:])
}
