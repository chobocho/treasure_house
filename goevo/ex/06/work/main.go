// 슬라이드 p6-v118-work — 작업 공간이 이웃 모듈을 찾아 준다, Go 1.18
package main

import (
	"fmt"

	"example.com/greet" // no require line, no replace line
)

func main() {
	fmt.Println(greet.Hello("workspace"))
}
