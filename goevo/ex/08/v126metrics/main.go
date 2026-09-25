// 슬라이드 p8-v126-metrics — runtime/metrics 의 스케줄러 지표, Go 1.26
package main

import (
	"fmt"
	"runtime/metrics"
	"strings"
	"sync"
)

func main() {
	var names []string
	for _, d := range metrics.All() {
		if strings.HasPrefix(d.Name, "/sched/goroutines/") ||
			strings.HasPrefix(d.Name, "/sched/goroutines-") ||
			strings.HasPrefix(d.Name, "/sched/threads") {
			names = append(names, d.Name)
		}
	}
	for _, n := range names {
		fmt.Println(n)
	}

	// Start 100 goroutines, then read the "created" counter.
	const created = "/sched/goroutines-created:goroutines"
	s := []metrics.Sample{{Name: created}}
	metrics.Read(s)
	before := s[0].Value.Uint64()
	var wg sync.WaitGroup
	for range 100 {
		wg.Go(func() {})
	}
	wg.Wait()
	metrics.Read(s)
	fmt.Println("created by the loop:", s[0].Value.Uint64()-before)
}
