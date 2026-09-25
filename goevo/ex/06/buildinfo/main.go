// 슬라이드 p6-v118-buildinfo — 실행 파일에 박힌 빌드 설정, Go 1.18
package main

import (
	"fmt"
	"runtime/debug"
	"strings"
)

func main() {
	bi, ok := debug.ReadBuildInfo()
	if !ok {
		fmt.Println("no build info")
		return
	}
	fmt.Println("path:", bi.Path)
	fmt.Println("go:  ", bi.GoVersion) // new field in 1.18
	for _, s := range bi.Settings {    // new field in 1.18
		v := s.Value
		if s.Key == "DefaultGODEBUG" { // long: count only
			n := strings.Count(v, ",") + 1
			v = fmt.Sprintf("(%d settings)", n)
		}
		fmt.Printf("  %s=%s\n", s.Key, v)
	}
}
