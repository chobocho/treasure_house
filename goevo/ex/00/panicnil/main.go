// 슬라이드 p0-godebug — GODEBUG 기본값도 go 줄을 따른다, Go 1.21
package main

import "fmt"

func main() {
	defer func() {
		r := recover()
		fmt.Printf("recover() = %v (%T)\n", r, r)
	}()
	panic(nil)
}
