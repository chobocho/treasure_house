// 슬라이드 p5-v111-bce — 전이 관계로 지운 경계 검사, Go 1.11
package main

import "fmt"

// pick: i < j and j < len(s) together prove i < len(s).
func pick(s []int, i, j int) int {
	if 0 <= i && i < j && j < len(s) {
		return s[i] + s[j]
	}
	return -1
}

// tail: s[i-10] after checking i >= 10 and i < len(s).
func tail(s []int, i int) int {
	if i >= 10 && i < len(s) {
		return s[i-10]
	}
	return -1
}

// guess: nothing links k to len(s), so the check stays.
func guess(s []int, k int) int {
	return s[k]
}

func main() {
	s := make([]int, 20)
	fmt.Println(pick(s, 1, 2), tail(s, 15), guess(s, 3))
}
