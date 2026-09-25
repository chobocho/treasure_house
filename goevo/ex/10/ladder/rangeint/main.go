// 슬라이드 p10-ladder-3 — 정수에 대한 range, Go 1.22
package main

import "fmt"

func main() {
	for i := range 3 {
		fmt.Print(i)
	}
	fmt.Println()
}
