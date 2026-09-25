// 슬라이드 p7-v121-once — sync.OnceFunc·OnceValue·OnceValues, Go 1.21
package main

import (
	"fmt"
	"strconv"
	"sync"
)

var loads int

var config = sync.OnceValue(func() map[string]string {
	loads++ // runs once, however many goroutines ask
	return map[string]string{"port": "8080"}
})

var port = sync.OnceValues(func() (int, error) {
	return strconv.Atoi(config()["port"])
})

func main() {
	var wg sync.WaitGroup
	for i := 0; i < 10; i++ {
		wg.Add(1)
		go func() { defer wg.Done(); config() }()
	}
	wg.Wait()
	p, err := port()
	fmt.Println(loads, p, err)

	hello := sync.OnceFunc(func() { fmt.Println("hello once") })
	hello()
	hello()
}
