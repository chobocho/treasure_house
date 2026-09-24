// 슬라이드 p3-v14-filename — 파일 이름 태그는 밑줄 뒤에서만, Go 1.4
package main

import (
	"fmt"
	"runtime"
	"sort"
)

var built []string // each compiled file adds its own name

func main() {
	sort.Strings(built)
	fmt.Println(runtime.GOOS+"/"+runtime.GOARCH, "compiled:", built)
}
