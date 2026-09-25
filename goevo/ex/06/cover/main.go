// 슬라이드 p6-v120-cover — 테스트가 아닌 프로그램의 커버리지, Go 1.20
package main

import (
	"fmt"
	"os"
)

func grade(n int) string {
	if n >= 90 {
		return "A"
	}
	return "B" // no run below reaches this line
}

func main() {
	for _, arg := range os.Args[1:] {
		if arg == "-h" {
			fmt.Println("usage: cover [-h]")
			return
		}
	}
	fmt.Println(grade(95))
}
