// 슬라이드 p4-v16-http2 — 투명한 HTTP/2, Go 1.6
package main

import (
	"fmt"
	"net/http"
	"net/http/httptest"
)

func main() {
	h := func(w http.ResponseWriter, r *http.Request) {
		fmt.Fprint(w, r.Proto)
	}
	// A TLS test server on 127.0.0.1 that offers "h2".
	srv := httptest.NewUnstartedServer(http.HandlerFunc(h))
	srv.EnableHTTP2 = true
	srv.StartTLS()
	defer srv.Close()

	res, err := srv.Client().Get(srv.URL)
	if err != nil {
		fmt.Println("error:", err)
		return
	}
	defer res.Body.Close()
	fmt.Println("client sees:", res.Proto)
}
