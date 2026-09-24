// 슬라이드 p5-v117-semicolon — 쿼리의 ; 는 구분자가 아니다, Go 1.17
package main

import (
	"fmt"
	"net/url"
)

func main() {
	u, _ := url.Parse("https://example.com/?a=1;b=2&c=3")
	fmt.Println("Query():", u.Query())

	v, err := url.ParseQuery("a=1;b=2&c=3")
	fmt.Println("ParseQuery:", v, "|", err)

	fmt.Println("Has(c):", v.Has("c"), "Has(a):", v.Has("a"))
}
