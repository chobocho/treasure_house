// 슬라이드 p3-v11-small — sort.Reverse·TrimPrefix·Truncate, Go 1.1
package main

import (
	"fmt"
	"sort"
	"strings"
	"time"
)

func main() {
	xs := []int{3, 1, 4, 1, 5}
	sort.Sort(sort.Reverse(sort.IntSlice(xs)))
	fmt.Println(xs)

	fmt.Println(strings.TrimPrefix("go1.1rc2", "go"))
	fmt.Println(strings.TrimSuffix("main_test.go", "_test.go"))

	t := time.Date(2013, 5, 13, 9, 30, 15, 123456789, time.UTC)
	fmt.Println(t.Truncate(time.Second).Format(time.RFC3339Nano))
	fmt.Println(t.Round(time.Millisecond).Format(time.RFC3339Nano))
	fmt.Println("day of year:", t.YearDay())
}
