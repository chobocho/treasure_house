// 슬라이드 p3-v12-slice3 — 세 인덱스 슬라이스 a[i:j:k], Go 1.2
package main

import "fmt"

func main() {
	var array [10]int
	for i := range array {
		array[i] = i
	}

	s2 := array[2:4]   // len 2, cap 8 (to the end of array)
	s3 := array[2:4:7] // len 2, cap 5 (7-2)
	fmt.Println(s2, len(s2), cap(s2))
	fmt.Println(s3, len(s3), cap(s3))
	fmt.Println(s2[:8]) // reslicing reaches array[9]
	// s3[:8] would panic: the cap hides array[7:]

	// why: append on a two-index slice overwrites the array
	_ = append(s2, -1)
	fmt.Println("after append(s2):", array)

	// with cap == len, append must copy to a new array
	full := array[5:7:7]
	grown := append(full, -2)
	fmt.Println("after append(full):", array)
	fmt.Println("grown:", grown)
}
