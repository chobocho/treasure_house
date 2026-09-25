// 슬라이드 p7-v121-runtime — 스택 추적에 만든 고루틴의 ID, Go 1.21
package main

import (
	"fmt"
	"runtime"
	"strings"
)

func worker(done chan<- string) {
	buf := make([]byte, 1024)
	n := runtime.Stack(buf, false)
	done <- string(buf[:n])
}

func main() {
	done := make(chan string)
	go worker(done)
	for _, line := range strings.Split(<-done, "\n") {
		if !strings.HasPrefix(line, "\t") && line != "" {
			fmt.Println(line) // function lines only, no pc offsets
		}
	}
}
