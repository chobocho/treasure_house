// 슬라이드 p8-v126-url — url.Parse 의 콜론 검사·쿼리 개수 한도, Go 1.26
package main

import (
	"fmt"
	"net/url"
	"strings"
)

func main() {
	for _, s := range []string{
		"http://[::1]/",
		"http://::1/",
		"http://localhost:80:80/",
	} {
		u, err := url.Parse(s)
		if err != nil {
			fmt.Printf("%-24s error: %v\n", s, err)
			continue
		}
		fmt.Printf("%-24s host=%q\n", s, u.Host)
	}

	// 10001 query parameters, one more than the default limit.
	q := strings.Repeat("a=1&", 10000) + "a=1"
	v, err := url.ParseQuery(q)
	fmt.Println("params:", len(v["a"]), "err:", err)
}
