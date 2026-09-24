// 슬라이드 p3-v11-surrogate — 서로게이트 반쪽은 인코딩 오류, Go 1.1
package main

import (
	"fmt"
	"unicode/utf8"
)

func main() {
	r := rune(0xD800) // a surrogate half, built at run time
	fmt.Printf("%+q\n", string(r))
	fmt.Println(utf8.ValidRune(r), utf8.ValidRune(0xFFFD))

	// the same half written as raw UTF-8 bytes still compiles...
	s := "\xed\xa0\x80"
	for i, c := range s { // ...but decodes as RuneError, byte by byte
		fmt.Printf("%d:%U ", i, c)
	}
	fmt.Println()
}
