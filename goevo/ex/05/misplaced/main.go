// 슬라이드 p5-v115-directive — 엉뚱한 자리의 //go: 지시문, Go 1.15
package main

import "fmt"

//go:noinline
var limit = 10 // noinline means nothing for a variable

func main() {
	fmt.Println(limit)
}
