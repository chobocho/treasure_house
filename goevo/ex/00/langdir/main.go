// 슬라이드 p0-lang — go.mod 의 go 줄이 언어 버전을 정한다, Go 1.22
package main

import "fmt"

func main() {
	for i := range 3 {
		fmt.Print(i)
	}
	fmt.Println()
}
