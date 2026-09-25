// 슬라이드 p8-v125-wggo — sync.WaitGroup.Go, Go 1.25
package main

import (
	"fmt"
	"slices"
	"strings"
	"sync"
)

func main() {
	words := []string{"gopher", "bubble", "tea", "trace"}
	upper := make([]string, len(words))

	// Before 1.25: wg.Add(1); go func() { defer wg.Done(); ... }()
	// Now Go does the Add, the go statement and the Done for you.
	var wg sync.WaitGroup
	for i, w := range words {
		wg.Go(func() {
			upper[i] = strings.ToUpper(w)
		})
	}
	wg.Wait()
	fmt.Println(upper)
	want := []string{"GOPHER", "BUBBLE", "TEA", "TRACE"}
	fmt.Println(slices.Equal(upper, want))
}
