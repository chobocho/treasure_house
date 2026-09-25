// 슬라이드 p8-v126-http — 307 리디렉트·httptest 의 example.com, Go 1.26
package main

import (
	"fmt"
	"net/http"
	"net/http/httptest"
)

func main() {
	mux := http.NewServeMux()
	docs := func(w http.ResponseWriter, r *http.Request) {
		fmt.Fprintf(w, "docs for %s via %s", r.URL.Path, r.Host)
	}
	mux.HandleFunc("/docs/", docs)

	// ServeMux redirects /docs to /docs/. Which status code?
	rec := httptest.NewRecorder()
	mux.ServeHTTP(rec, httptest.NewRequest("POST", "/docs", nil))
	fmt.Println(rec.Code, http.StatusText(rec.Code),
		rec.Header().Get("Location"))

	// The test server's client sends example.com to the test server.
	srv := httptest.NewServer(mux)
	defer srv.Close()
	resp, err := srv.Client().Get("http://api.example.com/docs/")
	if err != nil {
		panic(err)
	}
	defer resp.Body.Close()
	var body [64]byte
	n, _ := resp.Body.Read(body[:])
	fmt.Println(resp.StatusCode, string(body[:n]))
}
