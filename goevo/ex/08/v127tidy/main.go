// 슬라이드 p8-v127-tidy — go mod tidy 가 require 묶음을 합친다, Go 1.27
package main

import (
	"example.com/alpha"
	"example.com/beta"
	"fmt"
)

func main() {
	fmt.Println(alpha.Name, beta.Name)
}
