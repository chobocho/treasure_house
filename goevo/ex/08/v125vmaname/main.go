// 슬라이드 p8-v125-vmaname — 익명 메모리 영역의 이름, Go 1.25
package main

import (
	"bufio"
	"fmt"
	"os"
	"strings"
)

func main() {
	f, err := os.Open("/proc/self/maps")
	if err != nil {
		fmt.Println(err)
		return
	}
	defer f.Close()
	seen := map[string]bool{}
	sc := bufio.NewScanner(f)
	for sc.Scan() {
		line := sc.Text()
		if i := strings.Index(line, "[anon: Go:"); i >= 0 {
			seen[line[i:]] = true
		}
	}
	// Which regions get a mapping of their own depends on the address
	// layout (the heap base is randomized), so "[anon: Go: heap]" comes
	// and goes between runs. Print only what every run shows.
	fmt.Println("Go-named mappings:", len(seen) > 0)
	im := seen["[anon: Go: immortal metadata]"]
	fmt.Println("immortal metadata:", im)
}
