// 슬라이드 p2-v10-delete — 내장 함수 delete, Go 1
package main

import "fmt"

func main() {
	m := map[string]int{"a": 1, "b": 2}
	delete(m, "a")
	delete(m, "zzz") // deleting a missing key is a no-op
	fmt.Println(len(m), m)
}
