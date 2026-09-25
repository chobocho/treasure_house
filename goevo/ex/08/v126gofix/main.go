// 슬라이드 p8-v126-gofix — go fix 의 현대화 도구(modernizer), Go 1.26
package main

import (
	"fmt"
	"strings"
)

func clamp(v int) int {
	x := v
	if x < 0 {
		x = 0
	}
	if x > 100 {
		x = 100
	}
	return x
}

func key(pair string) string {
	i := strings.Index(pair, "=")
	if i >= 0 {
		return pair[:i]
	}
	return pair
}

func show(vs ...interface{}) {
	for i := 0; i < len(vs); i++ {
		fmt.Print(vs[i], " ")
	}
	fmt.Println()
}

func main() {
	show(clamp(-5), clamp(50), clamp(500))
	show(key("go=1.26"), key("plain"))
}
