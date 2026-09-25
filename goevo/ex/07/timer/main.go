// 슬라이드 p7-v123-timer — 버퍼 없는 타이머 채널, Go 1.23
package main

import (
	"fmt"
	"time"
)

func main() {
	t := time.NewTimer(time.Millisecond)
	fmt.Println("len/cap:", len(t.C), cap(t.C))

	time.Sleep(10 * time.Millisecond) // the timer has expired
	// Reset without draining t.C first: no stale value survives.
	t.Reset(time.Hour)
	select {
	case <-t.C:
		fmt.Println("stale value from the old expiry")
	default:
		fmt.Println("no stale value")
	}
	fmt.Println("Stop reports active timer:", t.Stop())
}
