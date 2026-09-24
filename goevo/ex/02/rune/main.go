// 슬라이드 p2-v10-rune — 문자 리터럴의 기본 타입은 rune, Go 1
package main

import (
	"fmt"
	"unicode"
)

func main() {
	delta := 'δ' // delta has type rune
	var DELTA rune = unicode.ToUpper(delta)
	fmt.Printf("%T %T %c %c\n", delta, DELTA, delta, DELTA)
	var r rune = 'a'
	var i32 int32 = r // rune is an alias for int32
	fmt.Println(i32)
}
