// 슬라이드 p5-v113-panicmsg — 패닉이 인덱스와 길이를 말한다, Go 1.13
package main

import "fmt"

func try(name string, f func()) {
	defer func() { fmt.Printf("%-8s %v\n", name, recover()) }()
	f()
}

func main() {
	s := []int{10}
	i, j, k := 3, 5, 0
	try("index", func() { _ = s[i] })
	try("slice", func() { _ = s[:j] })
	try("slice3", func() { _ = s[1:k] })
	try("string", func() { _ = "go"[i] })
}
