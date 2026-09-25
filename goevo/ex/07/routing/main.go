// 슬라이드 p7-v122-routing — ServeMux 의 새 패턴, Go 1.22
package main

import (
	"fmt"
	"net/http"
	"net/http/httptest"
	"strings"
)

func show(label string) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		fmt.Fprintf(w, "%s id=%q path=%q", label,
			r.PathValue("id"), r.PathValue("path"))
	}
}

func main() {
	mux := http.NewServeMux()
	mux.Handle("GET /items/{id}", show("get"))
	mux.Handle("POST /items/{id}", show("post"))
	mux.Handle("/files/{path...}", show("files"))
	mux.Handle("/exact/{$}", show("exact"))

	for _, req := range []string{
		"GET /items/42", "POST /items/7", "DELETE /items/7",
		"HEAD /items/1", "GET /files/a/b/c.txt",
		"GET /exact/", "GET /exact/more",
	} {
		var method, path string
		fmt.Sscan(req, &method, &path)
		rec := httptest.NewRecorder()
		mux.ServeHTTP(rec, httptest.NewRequest(method, path, nil))
		fmt.Printf("%-20s %d %s\n", req, rec.Code,
			strings.TrimSpace(rec.Body.String()))
	}
}
