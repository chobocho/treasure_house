// 슬라이드 p6-v118-anycomp — any 만 써도 go 1.18 필요, Go 1.18
package main

import "fmt"

func describe(v any) string { return fmt.Sprintf("%T", v) }

func main() {
	fmt.Println(describe(42), describe("go"))
}
