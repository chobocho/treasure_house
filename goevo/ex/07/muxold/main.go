// 슬라이드 p7-v122-muxgodebug — httpmuxgo121 로 옛 ServeMux, Go 1.22
package main

import (
	"fmt"
	"net/http"
	"net/http/httptest"
)

func showID(w http.ResponseWriter, r *http.Request) {
	fmt.Fprintf(w, "id=%q", r.PathValue("id"))
}

func main() {
	mux := http.NewServeMux()
	mux.HandleFunc("/items/{id}", showID)
	for _, p := range []string{"/items/42", "/items/%7Bid%7D"} {
		rec := httptest.NewRecorder()
		mux.ServeHTTP(rec, httptest.NewRequest("GET", p, nil))
		fmt.Printf("%-16s %d %q\n", p, rec.Code, rec.Body.String())
	}
}
