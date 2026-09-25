// 슬라이드 p7-v123-godebugmod — go.mod 의 godebug 지시문, Go 1.23
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
		for _, kv := range strings.Split(s.Value, ",") {
			switch strings.Split(kv, "=")[0] {
			case "panicnil", "httpmuxgo121", "winsymlink":
				fmt.Println(kv) // 1.21, 1.22 and 1.23 changes
			}
		}
	}
	defer func() { fmt.Println("recovered:", recover()) }()
	panic(nil)
}
