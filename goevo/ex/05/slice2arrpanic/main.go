// 슬라이드 p5-v117-slice2arr-2 — 처음으로 패닉할 수 있는 변환, Go 1.17
package main

import (
	"fmt"
	"reflect"
)

func main() {
	s := []int{1, 2, 3}
	t := reflect.TypeOf((*[4]int)(nil))

	// ConvertibleTo only looks at the types.
	fmt.Println("ConvertibleTo:", reflect.TypeOf(s).ConvertibleTo(t))
	// CanConvert (Go 1.17) also looks at the length.
	fmt.Println("CanConvert:   ", reflect.ValueOf(s).CanConvert(t))

	defer func() { fmt.Println("recovered:", recover()) }()
	p := (*[4]int)(s) // len(s) is 3 < 4
	fmt.Println(p)
}
