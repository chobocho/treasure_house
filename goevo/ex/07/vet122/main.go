// 슬라이드 p7-v122-vet — vet 의 새 검사 셋, Go 1.22
package main

import (
	"fmt"
	"log/slog"
	"time"
)

func work() {
	start := time.Now()
	defer fmt.Println("took", time.Since(start)) // evaluated now
	time.Sleep(time.Millisecond)
}

func main() {
	xs := []int{1}
	xs = append(xs) // appends nothing
	fmt.Println(xs)
	work()
	slog.Info("login", "user") // key without a value
}
