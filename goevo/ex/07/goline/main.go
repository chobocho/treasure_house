// 슬라이드 p7-v121-goline — go 줄은 최소 요구 버전, Go 1.21
package main

import (
	"fmt"
	"runtime"
)

func main() {
	fmt.Println("built by", runtime.Version())
}
