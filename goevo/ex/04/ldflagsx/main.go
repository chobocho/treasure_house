// 슬라이드 p4-v15-ldflagsx — 링커 -X, Go 1.5
package main

import "fmt"

// version is replaced at link time: -ldflags=-X=main.version=...
var version = "dev"

func main() {
	fmt.Println("version:", version)
}
