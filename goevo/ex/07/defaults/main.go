// 슬라이드 p7-v121-defaults — go 줄이 정하는 GODEBUG 기본값, Go 1.21
package main

import (
	"fmt"
	"runtime/debug"
	"strings"
)

func main() {
	bi, _ := debug.ReadBuildInfo()
	for _, s := range bi.Settings {
		if s.Key != "DefaultGODEBUG" {
			continue
		}
		// Only settings that differ from this toolchain's defaults.
		kvs := strings.Split(s.Value, ",")
		fmt.Println(len(kvs), "settings differ from go1.27 defaults")
		line := ""
		for _, kv := range kvs {
			if line != "" && len(line)+len(kv) >= 60 {
				fmt.Println(line)
				line = ""
			}
			if line != "" {
				line += " "
			}
			line += kv
		}
		fmt.Println(line)
	}
}
