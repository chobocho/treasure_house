// 슬라이드 p1-errors — 오류는 값이다, 1.27.1 에서의 동작
package main

import (
	"fmt"
	"strconv"
)

func parse(s string) (int, error) {
	n, err := strconv.Atoi(s)
	if err != nil {
		return 0, fmt.Errorf("parse %q: %v", s, err)
	}
	return n, nil
}

func main() {
	for _, s := range []string{"42", "4x2"} {
		n, err := parse(s)
		if err != nil {
			fmt.Println("error:", err)
			continue
		}
		fmt.Println("ok:", n)
	}
}
