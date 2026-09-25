// 슬라이드 p10-ladder-4 — new 에 식을 넘기기, Go 1.26
package main

import "fmt"

func main() {
	p := new(40 + 2)
	fmt.Println(*p)
}
