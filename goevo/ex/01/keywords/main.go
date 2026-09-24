// 슬라이드 p1-syntax — 키워드는 몇 개인가, 1.27.1 에서의 동작
package main

import (
	"fmt"
	"go/token"
)

func main() {
	var kw []string
	for t := token.Token(0); t < 200; t++ {
		if t.IsKeyword() {
			kw = append(kw, t.String())
		}
	}
	fmt.Println(len(kw), "keywords")
	fmt.Println(kw)
}
