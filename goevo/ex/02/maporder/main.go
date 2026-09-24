// 슬라이드 p2-v10-maporder — map 순회 차례는 예측 불가, Go 1
package main

import "fmt"

func main() {
	m := map[string]int{}
	for i := 0; i < 8; i++ {
		m[fmt.Sprint("k", i)] = i
	}
	firsts := map[string]bool{}
	for run := 0; run < 100; run++ {
		for k := range m {
			firsts[k] = true // first key of this loop
			break
		}
	}
	fmt.Println("100 loops, distinct first keys > 1:",
		len(firsts) > 1)
}
