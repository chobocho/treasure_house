// 슬라이드 p8-v127-leak — goroutineleak 프로파일, Go 1.27
package main

import (
	"fmt"
	"runtime/pprof"
	"strings"
	"time"
)

// leak starts a goroutine blocked on a channel no one can reach.
func leak() {
	ch := make(chan int)
	go func() { <-ch }()
}

func main() {
	for range 3 {
		leak()
	}
	time.Sleep(50 * time.Millisecond) // let them block

	var sb strings.Builder
	pprof.Lookup("goroutineleak").WriteTo(&sb, 1)
	head, _, _ := strings.Cut(sb.String(), "\n")
	fmt.Println(head)
	fmt.Println("mentions leak.func1:",
		strings.Contains(sb.String(), "main.leak.func1"))
}
