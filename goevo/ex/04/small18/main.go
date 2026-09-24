// 슬라이드 p4-v18-small — URL 호스트와 JSON 실수, Go 1.8
package main

import (
	"encoding/json"
	"fmt"
	"net/url"
)

func main() {
	u, _ := url.Parse("https://[::1]:8443/path")
	fmt.Println(u.Host, "->", u.Hostname(), u.Port())

	// JSON numbers now follow the ES6 formatting rules.
	for _, f := range []float64{1e20, 1e21, 0.000001, 0.0000001} {
		b, _ := json.Marshal(f)
		fmt.Println(string(b))
	}
}
