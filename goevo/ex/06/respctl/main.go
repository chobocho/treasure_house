// 슬라이드 p6-v120-respctl — http.ResponseController, Go 1.20
package main

import (
	"bufio"
	"fmt"
	"net/http"
	"net/http/httptest"
	"time"
)

func handler(w http.ResponseWriter, r *http.Request) {
	rc := http.NewResponseController(w)
	// Per-request deadline: zero time lifts the server's WriteTimeout.
	fmt.Println("SetWriteDeadline:", rc.SetWriteDeadline(time.Time{}))
	for i := 1; i <= 3; i++ {
		fmt.Fprintf(w, "chunk %d\n", i)
		// No w.(http.Flusher) type assertion needed any more.
		if err := rc.Flush(); err != nil {
			fmt.Println("flush:", err)
		}
	}
}

func main() {
	srv := httptest.NewUnstartedServer(http.HandlerFunc(handler))
	srv.Config.WriteTimeout = time.Second
	srv.Start() // loopback only
	defer srv.Close()

	resp, err := http.Get(srv.URL)
	if err != nil {
		panic(err)
	}
	defer resp.Body.Close()
	sc := bufio.NewScanner(resp.Body)
	for sc.Scan() {
		fmt.Println("client got:", sc.Text())
	}
	fmt.Println("chunked:", resp.TransferEncoding)
}
