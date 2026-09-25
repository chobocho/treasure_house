// 슬라이드 p6-v118-constraintonly — 제약 전용 인터페이스, Go 1.18
package main

import "fmt"

type Number interface{ ~int | ~float64 }

func main() {
	var n Number = 3     // a type set is not a value type
	var c comparable = 4 // neither is comparable
	fmt.Println(n, c)
}
