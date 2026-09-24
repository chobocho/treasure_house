// 슬라이드 p4-v18-gopath — GOPATH 기본값, Go 1.8
package main

import (
	"fmt"
	"go/build"
)

func main() {
	// With GOPATH unset, go/build falls back to $HOME/go.
	fmt.Println("GOPATH:", build.Default.GOPATH)
}
