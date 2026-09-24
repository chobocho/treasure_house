// 슬라이드 p4-v16-mapmisuse — 맵 동시 쓰기 감지, Go 1.6
package main

import "sync"

func main() {
	m := map[int]int{}
	var wg sync.WaitGroup
	for g := 0; g < 4; g++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for i := 0; i < 1000000; i++ {
				m[i%100] = i // unsynchronised write: a bug
			}
		}()
	}
	wg.Wait()
}
