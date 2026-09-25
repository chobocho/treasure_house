// 슬라이드 p8-v125-typeassert — reflect.TypeAssert, Go 1.25
package main

import (
	"fmt"
	"reflect"
	"testing"
	"time"
)

type Event struct {
	At   time.Time
	Name string
}

var sink time.Time

func main() {
	ev := &Event{Name: "deploy"}
	v := reflect.ValueOf(ev).Elem().Field(0) // addressable

	// Old way: box the value into an interface, then assert.
	old := testing.AllocsPerRun(100, func() {
		sink = v.Interface().(time.Time)
	})
	// New way: straight from reflect.Value to a Go value.
	now := testing.AllocsPerRun(100, func() {
		sink, _ = reflect.TypeAssert[time.Time](v)
	})
	fmt.Printf("v.Interface().(time.Time): %.0f allocs\n", old)
	fmt.Printf("reflect.TypeAssert:        %.0f allocs\n", now)

	_, ok := reflect.TypeAssert[string](v)
	fmt.Println("as string:", ok)
	s, ok := reflect.TypeAssert[fmt.Stringer](v)
	fmt.Println("as fmt.Stringer:", ok, s.String()[:10])
}
