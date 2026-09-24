// 슬라이드 p9-v128-newapi — 1.28 초안의 새 API 를 1.27.1 로, Go 1.28
package main

import (
	"flag"
	"fmt"
	"net/http"
	"net/url"
)

func main() {
	u := url.MustParse("https://go.dev/doc/")
	fmt.Println(u.Host, http.MethodQuery)
	for f := range flag.CommandLine.All() {
		fmt.Println(f.Name)
	}
}
