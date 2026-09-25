// 슬라이드 p8-v125-repanic — 다시 던진 패닉의 출력, Go 1.25
package main

import "fmt"

func cleanup() {
	if r := recover(); r != nil {
		fmt.Println("recovered:", r, "- rolling back")
		panic(r) // same value again
	}
}

func main() {
	defer cleanup()
	panic("PANIC")
}
