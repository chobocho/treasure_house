// 슬라이드 p5-v116-constraint — 두 문법을 다 읽는 패키지, Go 1.16
package main

import (
	"fmt"
	"go/build/constraint"
)

func main() {
	lines := []string{
		"// +build linux,arm64 darwin,!cgo",
		"//go:build (linux && arm64) || (darwin && !cgo)",
	}
	tags := map[string]bool{"linux": true, "arm64": true}
	has := func(tag string) bool { return tags[tag] }

	for _, l := range lines {
		expr, err := constraint.Parse(l)
		if err != nil {
			fmt.Println(err)
			continue
		}
		fmt.Printf("%-50s -> %v\n", expr.String(), expr.Eval(has))
	}
}
