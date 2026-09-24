// 슬라이드 p5-v112-buildinfo — 실행 파일이 아는 자기 모듈, Go 1.12
package main

import (
	"fmt"
	"runtime/debug"
)

func main() {
	bi, ok := debug.ReadBuildInfo()
	if !ok {
		fmt.Println("no build info (not built in module mode)")
		return
	}
	fmt.Println("main package:", bi.Path)
	fmt.Println("main module: ", bi.Main.Path, bi.Main.Version)
	fmt.Println("dependencies:", len(bi.Deps))
}
