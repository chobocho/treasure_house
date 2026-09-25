// 슬라이드 p6-v120-rewrite — ReverseProxy 의 Rewrite 훅, Go 1.20
package main

import (
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
	"net/http/httputil"
	"net/url"
	"os"
)

func main() {
	// The backend reports what the proxy sent it (loopback only).
	var target *url.URL
	backend := httptest.NewServer(http.HandlerFunc(
		func(w http.ResponseWriter, r *http.Request) {
			fmt.Fprintln(w, "path:", r.URL.Path)
			fmt.Fprintln(w, "Host is backend:", r.Host == target.Host)
			for _, h := range []string{"X-Forwarded-For",
				"X-Forwarded-Proto", "X-Via"} {
				fmt.Fprintf(w, "%s: %s\n", h, r.Header.Get(h))
			}
		}))
	defer backend.Close()
	target, _ = url.Parse(backend.URL + "/api")

	proxy := httptest.NewServer(&httputil.ReverseProxy{
		Rewrite: func(r *httputil.ProxyRequest) {
			r.SetURL(target) // route, and set the outbound Host
			r.SetXForwarded()
			r.Out.Header.Set("X-Via", "rewrite-hook")
		},
	})
	defer proxy.Close()

	resp, err := http.Get(proxy.URL + "/users")
	if err != nil {
		panic(err)
	}
	defer resp.Body.Close()
	io.Copy(os.Stdout, resp.Body)
}
