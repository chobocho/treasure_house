// 슬라이드 p8-v125-csrf — net/http.CrossOriginProtection, Go 1.25
package main

import (
	"fmt"
	"net/http"
	"net/http/httptest"
)

func main() {
	mux := http.NewServeMux()
	mux.HandleFunc("/transfer",
		func(w http.ResponseWriter, r *http.Request) {
			fmt.Fprint(w, "ok")
		})
	cop := http.NewCrossOriginProtection()
	cop.AddTrustedOrigin("https://partner.example")
	h := cop.Handler(mux)

	try := func(method, site, origin string) {
		url := "https://bank.example/transfer"
		r := httptest.NewRequest(method, url, nil)
		if site != "" {
			r.Header.Set("Sec-Fetch-Site", site)
		}
		if origin != "" {
			r.Header.Set("Origin", origin)
		}
		w := httptest.NewRecorder()
		h.ServeHTTP(w, r)
		fmt.Printf("%-4s %-11s %-25q -> %d\n",
			method, site, origin, w.Code)
	}
	try("POST", "same-origin", "")
	try("POST", "cross-site", "https://evil.example")
	try("GET", "cross-site", "https://evil.example") // safe method
	try("POST", "cross-site", "https://partner.example")
	try("POST", "", "https://evil.example") // no Sec-Fetch-Site
	try("POST", "", "")                     // curl, not a browser
}
