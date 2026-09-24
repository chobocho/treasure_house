// 슬라이드 p1-noimplicit — 암묵적인 수 변환은 없다, 1.27.1 에서의 동작
package main

import "fmt"

func main() {
	var i int = 1
	var i64 int64 = 2
	var f float64 = 0.5
	fmt.Println(i + i64)
	fmt.Println(f * i)
}
