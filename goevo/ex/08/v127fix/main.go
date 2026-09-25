// 슬라이드 p8-v127-fix — go fix 의 새 modernizer, Go 1.27
package main

import (
	"fmt"
	"sync/atomic"
)

var hits int64 // updated only through sync/atomic

func main() {
	for range 3 {
		atomic.AddInt64(&hits, 1)
	}
	words := []string{"a", "b", "c"}
	for i := len(words) - 1; i >= 0; i-- {
		fmt.Print(words[i], " ")
	}
	fmt.Println(atomic.LoadInt64(&hits))
}
