// 슬라이드 p7-v121-sortfunc — cmp 패키지와 SortFunc, Go 1.21
package main

import (
	"cmp"
	"fmt"
	"math"
	"slices"
	"strings"
)

type Person struct {
	Name string
	Age  int
}

func main() {
	people := []Person{{"Eve", 30}, {"bob", 25}, {"Al", 30}, {"Cy", 25}}
	// Age descending, then name case-insensitively.
	slices.SortFunc(people, func(a, b Person) int {
		if c := cmp.Compare(b.Age, a.Age); c != 0 {
			return c
		}
		return strings.Compare(strings.ToLower(a.Name),
			strings.ToLower(b.Name))
	})
	fmt.Println(people)

	nan := math.NaN()
	fmt.Println(cmp.Compare(nan, math.Inf(-1)), cmp.Less(nan, 0.0))
	f := []float64{3, nan, 1}
	slices.Sort(f) // NaN sorts first
	fmt.Println(f)
}
