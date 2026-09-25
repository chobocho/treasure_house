// 슬라이드 p6-v118-unused — 클로저 안에서 대입만 한 변수, Go 1.18
package main

func main() {
	found := false
	check := func(x int) {
		if x > 2 {
			found = true // set, but never read anywhere
		}
	}
	check(3)
}
