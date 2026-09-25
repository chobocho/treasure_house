// 슬라이드 p6-v119-atomic — atomic.Int64 와 atomic.Pointer[T], Go 1.19
package main

import (
	"fmt"
	"sync"
	"sync/atomic"
)

type Config struct{ Version int }

type Server struct {
	hits atomic.Int64           // no plain int64 to touch by mistake
	cfg  atomic.Pointer[Config] // typed: no unsafe.Pointer casts
}

func main() {
	var s Server
	s.cfg.Store(&Config{Version: 1})

	var wg sync.WaitGroup
	for i := 0; i < 50; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			s.hits.Add(2)
		}()
	}
	wg.Wait()

	old := s.cfg.Swap(&Config{Version: 2})
	fmt.Println(s.hits.Load(), old.Version, s.cfg.Load().Version)

	var ready atomic.Bool
	fmt.Println(ready.CompareAndSwap(false, true), ready.Load())
}
