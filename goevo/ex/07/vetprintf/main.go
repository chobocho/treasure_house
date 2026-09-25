// 슬라이드 p7-v124-vetprintf — 상수가 아닌 서식 문자열, Go 1.24
package main

import "fmt"

func main() {
	msg := "disk 100% full"
	fmt.Printf(msg) // should be fmt.Print(msg)
	fmt.Println()
}
