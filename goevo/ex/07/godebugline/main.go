// 슬라이드 p7-v121-godebugline — //go:debug 지시문, Go 1.21
//go:debug panicnil=1

package main

import "fmt"

func main() {
	defer func() {
		r := recover()
		fmt.Printf("recovered %v (%T)\n", r, r)
	}()
	panic(nil)
}
