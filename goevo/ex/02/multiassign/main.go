// 슬라이드 p2-v10-multiassign — 다중 대입의 평가 차례, Go 1
package main

import "fmt"

func main() {
	sa := []int{1, 2, 3}
	i := 0
	i, sa[i] = 1, 2 // sets i = 1, sa[0] = 2

	sb := []int{1, 2, 3}
	j := 0
	sb[j], j = 2, 1 // sets sb[0] = 2, j = 1

	sc := []int{1, 2, 3}
	sc[0], sc[0] = 1, 2 // sc[0] = 1, then sc[0] = 2
	fmt.Println(i, sa, j, sb, sc)
}
