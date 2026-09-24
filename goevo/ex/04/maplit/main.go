// 슬라이드 p4-v15-maplit — 맵 리터럴 키 생략, Go 1.5
package main

import "fmt"

type Point struct{ Lat, Long float64 }

func main() {
	// Keys may omit their type, just like slice elements.
	m := map[Point]string{
		{29.935523, 52.891566}:   "Persepolis",
		{-25.352594, 131.034361}: "Uluru",
	}
	fmt.Println(m[Point{-25.352594, 131.034361}], len(m))

	// Pointer keys: {1, 2} means &Point{1, 2}.
	pm := map[*Point]string{{1, 2}: "p"}
	for k, v := range pm {
		fmt.Println(*k, v)
	}
	fmt.Println(len(old))
}
