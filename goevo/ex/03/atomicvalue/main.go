// 슬라이드 p3-v14-atomicvalue — atomic.Value 로 설정 교체, Go 1.4
package main

import (
	"fmt"
	"sync"
	"sync/atomic"
)

type Config struct {
	Name    string
	Workers int
}

var current atomic.Value // holds a *Config; never mutated in place

func load() *Config { return current.Load().(*Config) }

func main() {
	current.Store(&Config{Name: "v1", Workers: 2})

	var wg sync.WaitGroup
	results := make([]string, 4)
	for i := range results {
		wg.Add(1)
		go func(i int) { // readers take no lock
			defer wg.Done()
			c := load()
			results[i] = fmt.Sprint(c.Name, "/", c.Workers)
		}(i)
	}
	wg.Wait()
	fmt.Println(results)

	current.Store(&Config{Name: "v2", Workers: 8}) // swap whole
	fmt.Println(*load())

	defer func() { fmt.Println("recovered:", recover()) }()
	current.Store("oops") // every Store must use the same type
}
