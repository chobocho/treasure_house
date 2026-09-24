// 슬라이드 p3-v12-nil — nil 포인터를 거친 접근은 반드시 패닉, Go 1.2
package main

import "fmt"

type T struct {
	X     [1 << 24]byte // Field sits 16 MiB past the struct start
	Field int32
}

func read(x *T) (v int32, err interface{}) {
	defer func() { err = recover() }()
	return x.Field, nil // address 1<<24 if x is nil
}

func main() {
	var x *T
	_, err := read(x)
	fmt.Println("recovered:", err)

	var arr *[4]int
	func() {
		defer func() { fmt.Println("recovered:", recover()) }()
		fmt.Println(len(arr)) // fine: len of *array is a constant
		fmt.Println(arr[2])   // indirection through nil: panics
	}()
}
