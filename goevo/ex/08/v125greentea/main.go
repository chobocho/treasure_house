// 슬라이드 p8-v125-greentea — 실험 GC 그린티, Go 1.25
package main

import (
	"fmt"
	"runtime/debug"
)

// The GC is chosen at build time, not at run time: the choice is
// recorded in the binary's build settings like any GOEXPERIMENT.
func main() {
	exp := "(none)"
	if bi, ok := debug.ReadBuildInfo(); ok {
		for _, s := range bi.Settings {
			if s.Key == "GOEXPERIMENT" {
				exp = s.Value
			}
		}
	}
	fmt.Println("GOEXPERIMENT at build:", exp)
}
