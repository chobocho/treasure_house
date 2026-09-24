// 슬라이드 p3-v14-generate — go generate 가 돌리는 지시 주석, Go 1.4
package main

import "fmt"

//go:generate go run ./gen -n 6 -o squares.go

func main() {
	fmt.Println(squares) // defined in the generated squares.go
}
