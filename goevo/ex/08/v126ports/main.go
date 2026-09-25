// 슬라이드 p8-v126-ports — 포트의 변화(교차 빌드로 확인), Go 1.26
package main

import (
	"fmt"
	"runtime"
)

func main() {
	fmt.Println(runtime.GOOS, runtime.GOARCH)
}
