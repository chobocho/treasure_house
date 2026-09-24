// 슬라이드 p2-v10-append — 문자열을 []byte 에 바로 append, Go 1
package main

import "fmt"

func main() {
	greeting := []byte{}
	greeting = append(greeting, []byte("hello ")...) // before Go 1
	greeting = append(greeting, "world"...)          // Go 1
	fmt.Println(string(greeting))
}
