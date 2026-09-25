// 슬라이드 p6-v120-structcmp — 필드 순서대로 비교, Go 1.20
package main

import "fmt"

type pair struct{ A, B any }

func eq(x, y pair) (r string) {
	defer func() {
		if e := recover(); e != nil {
			r = fmt.Sprint("panic: ", e)
		}
	}()
	return fmt.Sprint(x == y)
}

func main() {
	// func values are not comparable
	f := func() {}
	fmt.Println(eq(pair{1, f}, pair{2, f})) // A differs: B unread
	fmt.Println(eq(pair{1, f}, pair{1, f})) // A equal: B compared
}
