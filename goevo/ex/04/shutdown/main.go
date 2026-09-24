// 슬라이드 p4-v18-shutdown — 우아한 종료, Go 1.8
package main

import (
	"context"
	"fmt"
	"io"
	"net"
	"net/http"
)

func main() {
	ln, err := net.Listen("tcp", "127.0.0.1:0") // loopback only
	if err != nil {
		panic(err)
	}
	h := func(w http.ResponseWriter, r *http.Request) {
		fmt.Fprint(w, "hello")
	}
	srv := &http.Server{Handler: http.HandlerFunc(h)}
	done := make(chan error)
	go func() { done <- srv.Serve(ln) }()

	res, err := http.Get("http://" + ln.Addr().String())
	if err != nil {
		panic(err)
	}
	body, _ := io.ReadAll(res.Body)
	res.Body.Close()
	fmt.Println("got:", string(body))

	// Stop accepting, wait for active requests, then return.
	fmt.Println("Shutdown:", srv.Shutdown(context.Background()))
	fmt.Println("Serve:", <-done)
}
