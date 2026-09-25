// 슬라이드 p7-v122-small — cmp.Or·Concat·TypeFor, Go 1.22
package main

import (
	"cmp"
	"fmt"
	"reflect"
	"slices"
)

type Config struct{ Host string }

func main() {
	env, flag := "", "example.org"
	fmt.Println(cmp.Or(env, flag, "localhost")) // first non-zero

	fmt.Println(slices.Concat([]int{1}, []int{2, 3}, nil, []int{4}))

	fmt.Println(reflect.TypeFor[Config]())
	fmt.Println(reflect.TypeOf((*error)(nil)).Elem()) // the old way
	fmt.Println(reflect.TypeFor[error]())
}
