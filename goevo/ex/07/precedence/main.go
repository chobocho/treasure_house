// 슬라이드 p7-v122-precedence — 구체적인 패턴이 이긴다, Go 1.22
package main

import (
	"fmt"
	"net/http"
	"net/http/httptest"
)

func named(s string) http.HandlerFunc {
	return func(w http.ResponseWriter, _ *http.Request) {
		fmt.Fprint(w, s)
	}
}

func main() {
	mux := http.NewServeMux()
	mux.Handle("/items/{id}", named("any item"))
	mux.Handle("/items/latest", named("latest")) // more specific

	for _, p := range []string{"/items/latest", "/items/9"} {
		rec := httptest.NewRecorder()
		mux.ServeHTTP(rec, httptest.NewRequest("GET", p, nil))
		fmt.Println(p, "->", rec.Body)
	}

	defer func() { fmt.Println("panic:", recover()) }()
	// GET is narrower in method, but broader in path: neither wins.
	mux.Handle("GET /items/{id}", named("GET item"))
}
