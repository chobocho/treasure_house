// 슬라이드 p5-v112-small — reflect.Value.MapRange, Go 1.12
package main

import (
	"fmt"
	"reflect"
	"sort"
)

// keysOf works on any map, whatever its key and value types.
func keysOf(m interface{}) []string {
	var out []string
	it := reflect.ValueOf(m).MapRange()
	for it.Next() {
		out = append(out, fmt.Sprint(it.Key(), "=", it.Value()))
	}
	sort.Strings(out)
	return out
}

func main() {
	fmt.Println(keysOf(map[string]int{"b": 2, "a": 1}))
	fmt.Println(keysOf(map[int]bool{3: true, 1: false}))
}
