// 슬라이드 p7-v122-loopvar — 반복마다 새 루프 변수, Go 1.22
package main

import "fmt"

func main() {
	var prints []func()
	for i := 1; i <= 3; i++ {
		prints = append(prints, func() { fmt.Print(i, " ") })
	}
	for _, v := range []string{"a", "b", "c"} {
		prints = append(prints, func() { fmt.Print(v, " ") })
	}
	for _, p := range prints {
		p()
	}
	fmt.Println()
}
