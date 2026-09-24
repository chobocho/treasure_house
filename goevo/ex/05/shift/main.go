// 슬라이드 p5-v113-shift — 부호 있는 시프트 횟수, Go 1.13
package main

import "fmt"

func main() {
	for n := 0; n < 4; n++ { // n is an int, not a uint
		fmt.Print(1<<n, " ")
	}
	fmt.Println()

	defer func() { fmt.Println("recovered:", recover()) }()
	n := -1
	fmt.Println(1 << n) // a negative count panics at run time
}
