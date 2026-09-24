// 슬라이드 p5-v112-langver — go 줄이 언어 버전이 되다, Go 1.12
package main

import "fmt"

type Celsius = float64 // type alias: a Go 1.9 feature

func main() {
	var c Celsius = 36.5
	var f float64 = c // same type, no conversion needed
	fmt.Println(f)
}
