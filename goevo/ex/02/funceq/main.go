// 슬라이드 p2-v10-equality — 함수·map 의 같음은 nil 과만, Go 1
package main

import "fmt"

func main() {
	f := func() {}
	g := func() {}
	m1 := map[int]int{}
	m2 := map[int]int{}
	fmt.Println(f == nil, m1 == nil) // still legal
	fmt.Println(f == g)              // illegal since Go 1
	fmt.Println(m1 == m2)            // illegal since Go 1
}
