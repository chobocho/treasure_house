// 슬라이드 p8-v125-vmaname — 익명 메모리 영역의 이름, Go 1.25
package main

import (
	"bufio"
	"fmt"
	"os"
	"slices"
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
	names := make([]string, 0, len(seen))
	for n := range seen {
		names = append(names, n)
	}
	slices.Sort(names)
	fmt.Println(len(names), "distinct Go mapping names")
	for _, n := range names {
		fmt.Println(" ", n)
	}
}
