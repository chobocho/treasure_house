// 슬라이드 p3-v14-small — map 포인터·µs·Comparable, Go 1.4
package main

import (
	"fmt"
	"reflect"
	"time"
)

func main() {
	// pointers to maps now print like pointers to structs
	fmt.Println(&map[string]int{"one": 1})
	fmt.Println(&struct{ A int }{1})

	// durations use the micro sign; "us" is still accepted on input
	d := 1500 * time.Nanosecond
	fmt.Println(d)
	p, err := time.ParseDuration("3us")
	fmt.Println(p, err)

	// which types support == ?
	for _, v := range []interface{}{1, "s", []int{}, map[int]int{}} {
		t := reflect.TypeOf(v)
		fmt.Printf("%-12v comparable=%v\n", t, t.Comparable())
	}
}
