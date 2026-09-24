// 슬라이드 p9-v128-proxy — 대·소문자 프록시 변수가 다를 때, Go 1.28
package main

import (
	"fmt"
	"net/http"
)

func main() {
	req, _ := http.NewRequest("GET", "http://example.com/", nil)
	u, err := http.ProxyFromEnvironment(req)
	fmt.Println("proxy:", u, err)
}
