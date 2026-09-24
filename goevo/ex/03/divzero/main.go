// 슬라이드 p3-v11-divzero — 상수 0 나눗셈은 컴파일 오류, Go 1.1
package main

import "fmt"

func f(x int) int {
	return x / 0 // Go 1.0: run-time panic. Go 1.1: compile error
}

func g(x, zero int) int {
	return x / zero // a variable zero still panics at run time
}

func main() {
	fmt.Println(f(1), g(1, 0))
}
