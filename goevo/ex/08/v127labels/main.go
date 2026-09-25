// 슬라이드 p8-v127-labels — 트레이스백 머리 줄의 고루틴 라벨, Go 1.27
package main

import (
	"context"
	"fmt"
	"runtime"
	"runtime/pprof"
	"strings"
)

// header returns the first line of this goroutine's traceback.
func header() string {
	buf := make([]byte, 1<<10)
	stack := string(buf[:runtime.Stack(buf, false)])
	line, _, _ := strings.Cut(stack, "\n")
	return line
}

func main() {
	labels := pprof.Labels("request", "r-42", "user", "gopher")
	pprof.Do(context.Background(), labels, func(context.Context) {
		fmt.Println(header())
	})
}
