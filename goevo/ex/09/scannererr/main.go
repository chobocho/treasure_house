// 슬라이드 p9-v128-vet — 스캐너 오류를 안 보는 루프, Go 1.28
package main

import (
	"bufio"
	"fmt"
	"strings"
)

func main() {
	sc := bufio.NewScanner(strings.NewReader("a\nb\n"))
	for sc.Scan() {
		fmt.Println(sc.Text())
	}
	// sc.Err() is never checked: an I/O error would go unreported.
}
