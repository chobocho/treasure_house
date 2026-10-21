// 카드를 한 번 받고, 받은 ETag 으로 조건부 GET 을 한 번 더 한다.
// net/http 만 — 서버가 캐시 머리글을 어떻게 다는지 보려는 것.
//
//	go run ./03/card_cache 카드주소...
package main

import (
	"fmt"
	"io"
	"net/http"
	"os"
	"strings"
)

const wellKnown = "/.well-known/agent-card.json"

// region: get
func get(url, etag string) (*http.Response, error) {
	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		return nil, err
	}
	if etag != "" {
		req.Header.Set("If-None-Match", etag)
	}
	res, err := http.DefaultClient.Do(req)
	if err != nil {
		return nil, err
	}
	defer res.Body.Close()
	_, err = io.Copy(io.Discard, res.Body)
	return res, err
}

// endregion

// orDash 는 빈 머리글을 "-" 로 찍는다.
func orDash(s string) string {
	if s == "" {
		return "-"
	}
	return s
}

// region: main
func main() {
	for _, base := range os.Args[1:] {
		url := strings.TrimSuffix(base, "/") + wellKnown
		first, err := get(url, "")
		if err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
		etag := first.Header.Get("ETag")
		fmt.Println(base)
		fmt.Printf("  GET → %d · ETag %s\n",
			first.StatusCode, orDash(etag))
		cc := first.Header.Get("Cache-Control")
		fmt.Printf("    Cache-Control %s\n", orDash(cc))
		if etag == "" {
			fmt.Println("  ETag 이 없다 — 조건부로 물을 수 없다")
			continue
		}
		again, err := get(url, etag)
		if err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
		fmt.Printf("  GET If-None-Match → %d\n", again.StatusCode)
	}
}

// endregion
//@ norun
