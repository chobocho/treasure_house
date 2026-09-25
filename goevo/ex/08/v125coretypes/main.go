// 슬라이드 p8-v125-coretypes — 명세에서 core type 을 지우다, Go 1.25
package main

import "fmt"

// Fine: every type in the set can be sliced.
func tail[S ~[]byte | ~string](s S) S { return s[1:] }

// Not fine: close is not allowed on a receive-only channel.
func closeAll[C chan int | <-chan int](c C) { close(c) }

// Not fine: one type in the set cannot be sliced.
func head[T []int | map[int]int](x T) T { return x[:1] }

func main() {
	fmt.Println(tail("xgo"), string(tail([]byte("xgo"))))
}
