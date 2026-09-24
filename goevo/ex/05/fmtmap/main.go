// 슬라이드 p5-v112-fmtmap — map 을 키 차례로 찍는다, Go 1.12
package main

import (
	"fmt"
	"math"
)

func main() {
	m := map[string]int{"pear": 3, "apple": 1, "fig": 2, "kiwi": 4}
	fmt.Println(m)

	f := map[float64]string{2: "two", math.NaN(): "nan", -1: "minus"}
	fmt.Println(f)

	mixed := map[interface{}]int{"b": 1, 2: 2, "a": 3, 1: 4}
	fmt.Printf("%v\n", mixed)
}
