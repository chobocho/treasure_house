// 슬라이드 p0-machine — 이 덱을 만든 기계의 go, Go 1.27
package main

import (
	"fmt"
	"runtime"
)

func main() {
	fmt.Println(runtime.Version(), runtime.GOOS+"/"+runtime.GOARCH)
}
