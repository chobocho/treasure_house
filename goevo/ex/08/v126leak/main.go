// 슬라이드 p8-v126-leak — 고루틴 누수 프로파일(1.26 실험), Go 1.26
package main

import (
	"errors"
	"fmt"
	"runtime/pprof"
	"strings"
	"time"
)

func work(w int) error {
	if w == 2 {
		return errors.New("bad item")
	}
	time.Sleep(50 * time.Millisecond)
	return nil
}

func process(ws []int) error {
	ch := make(chan error) // unbuffered
	for _, w := range ws {
		go func() { ch <- work(w) }()
	}
	for range len(ws) {
		if err := <-ch; err != nil {
			return err // early return: the other senders block forever
		}
	}
	return nil
}

func main() {
	fmt.Println("process:", process([]int{1, 2, 3, 4, 5}))
	time.Sleep(200 * time.Millisecond) // let the senders block
	var b strings.Builder
	pprof.Lookup("goroutineleak").WriteTo(&b, 1)
	for _, line := range strings.Split(b.String(), "\n") {
		if f := strings.Fields(line); len(f) == 4 && f[0] == "#" {
			fmt.Println("  ", f[2], f[3]) // "# pc func file:line"
		} else if strings.HasPrefix(line, "goroutineleak") {
			fmt.Println(line)
		}
	}
}
