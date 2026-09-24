// 슬라이드 p1-deps — 쓰지 않는 의존은 컴파일 오류, 1.27.1 에서의 동작
package main

import (
	"fmt"
	"os"
)

func main() {
	fmt.Println("hello")
}
