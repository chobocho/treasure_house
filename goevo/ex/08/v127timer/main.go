// 슬라이드 p8-v127-timer — asynctimerchan 이 사라졌다, Go 1.27
package main

import (
	"fmt"
	"time"
)

func main() {
	t := time.NewTimer(time.Hour)
	// Unbuffered (synchronous) timer channels, always, since 1.27.
	fmt.Println("cap(t.C) =", cap(t.C))
	t.Stop()
}
