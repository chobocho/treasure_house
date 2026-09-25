// 슬라이드 p10-ladder-3 — min·max·clear 내장 함수, Go 1.21
package main

import "fmt"

func main() {
	m := map[string]int{"a": 1}
	clear(m)
	fmt.Println(min(3, 1, 2), max(3, 1, 2), len(m))
}
