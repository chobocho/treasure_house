// 슬라이드 p4-v19-syncmap — sync.Map, Go 1.9
package main

import (
	"fmt"
	"sort"
	"sync"
)

func main() {
	var m sync.Map // zero value is ready; no make, no mutex
	var wg sync.WaitGroup
	for i := 0; i < 4; i++ {
		wg.Add(1)
		go func(i int) {
			defer wg.Done()
			m.Store(i, i*i)
		}(i)
	}
	wg.Wait()

	v, ok := m.Load(3)
	fmt.Println("Load(3):", v, ok)
	actual, loaded := m.LoadOrStore(3, 100)
	fmt.Println("LoadOrStore(3):", actual, loaded)

	var keys []int
	m.Range(func(k, v interface{}) bool { // order is random
		keys = append(keys, k.(int))
		return true
	})
	sort.Ints(keys)
	fmt.Println("keys:", keys)
}
