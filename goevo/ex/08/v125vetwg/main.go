// 슬라이드 p8-v125-vetwg — vet 의 waitgroup·hostport 분석기, Go 1.25
package main

import (
	"fmt"
	"net"
	"sync"
)

func dial(host string, port int) (net.Conn, error) {
	addr := fmt.Sprintf("%s:%d", host, port) // breaks for IPv6
	return net.Dial("tcp", addr)
}

func main() {
	var wg sync.WaitGroup
	for i := range 3 {
		go func() {
			wg.Add(1) // too late: Wait may already have returned
			defer wg.Done()
			fmt.Println(i)
		}()
	}
	wg.Wait()
	_, _ = dial("::1", 8080)
}
