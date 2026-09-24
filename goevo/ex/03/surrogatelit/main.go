// 슬라이드 p3-v11-surrogate — 반쪽 리터럴은 컴파일 오류, Go 1.1
package main

import "fmt"

const r = '\ud800'
const s = "\ud800"

func main() {
	fmt.Println(r, s)
}
