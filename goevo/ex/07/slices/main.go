// 슬라이드 p7-v121-slices — slices 패키지, Go 1.21
package main

import (
	"fmt"
	"slices"
)

func main() {
	s := []int{5, 2, 8, 2, 9, 1}
	fmt.Println(slices.Contains(s, 8), slices.Index(s, 2))
	fmt.Println(slices.Min(s), slices.Max(s))

	slices.Sort(s)
	fmt.Println(s)
	i, found := slices.BinarySearch(s, 8)
	fmt.Println(i, found)

	s = slices.Compact(s) // drops consecutive duplicates
	fmt.Println(s)
	s = slices.Insert(s, 1, 100, 200)
	s = slices.Delete(s, 3, 5) // removes s[3:5]
	fmt.Println(s)

	c := slices.Clone(s)
	slices.Reverse(c)
	fmt.Println(c, slices.Equal(s, c))
}
