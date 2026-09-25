// 슬라이드 p6-v118-append — append 가 용량을 늘리는 공식, Go 1.18
package main

import "fmt"

func main() {
	var s []int64
	last := -1
	for i := 0; i < 3000; i++ {
		s = append(s, int64(i))
		if cap(s) != last { // print only when a new array was made
			if last > 0 {
				fmt.Printf("%5d → %5d  ×%.2f\n",
					last, cap(s), float64(cap(s))/float64(last))
			}
			last = cap(s)
		}
	}
}
