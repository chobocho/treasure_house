// 슬라이드 p3-v11-reflect — reflect 의 MakeFunc·Select 등, Go 1.1
package main

import (
	"fmt"
	"reflect"
)

// swap is filled in at run time by MakeFunc
var swap func(int, string) (string, int)

func main() {
	fn := func(in []reflect.Value) []reflect.Value {
		return []reflect.Value{in[1], in[0]}
	}
	v := reflect.ValueOf(&swap).Elem()
	v.Set(reflect.MakeFunc(v.Type(), fn))
	fmt.Println(swap(7, "seven"))

	// build the type []T from T alone
	t := reflect.SliceOf(reflect.TypeOf(1.5))
	fmt.Println(t, reflect.MapOf(reflect.TypeOf(""), t))

	// a Go conversion, done through reflect
	f := reflect.ValueOf(65).Convert(reflect.TypeOf(1.0))
	fmt.Println(f.Interface(), f.Kind())

	// a select statement built at run time
	ch := make(chan int, 1)
	ch <- 42
	cases := []reflect.SelectCase{
		{Dir: reflect.SelectRecv, Chan: reflect.ValueOf(ch)},
		{Dir: reflect.SelectDefault},
	}
	chosen, got, ok := reflect.Select(cases)
	fmt.Println(chosen, got, ok)
}
