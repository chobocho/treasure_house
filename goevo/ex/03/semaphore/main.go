// 슬라이드 p3-v13-memmodel — 버퍼 채널을 세마포어로, Go 1.3
package main

import (
	"fmt"
	"sync"
	"sync/atomic"
)

func main() {
	const limit = 3
	sem := make(chan struct{}, limit) // cap = max holders

	var running, peak int32
	var wg sync.WaitGroup
	for i := 0; i < 20; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			sem <- struct{}{}        // acquire: send
			defer func() { <-sem }() // release: receive

			n := atomic.AddInt32(&running, 1)
			for {
				p := atomic.LoadInt32(&peak)
				if n <= p || atomic.CompareAndSwapInt32(&peak, p, n) {
					break
				}
			}
			atomic.AddInt32(&running, -1)
		}()
	}
	wg.Wait()
	fmt.Println("peak <= limit:", atomic.LoadInt32(&peak) <= limit)
}
