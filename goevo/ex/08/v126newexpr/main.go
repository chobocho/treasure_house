// 슬라이드 p8-v126-newexpr — new(expr): 초깃값을 주는 new, Go 1.26
package main

import "fmt"

func main() {
	// Old form: the operand is a type, the variable starts at zero.
	a := new(int)

	// New form: the operand is an expression, the variable starts
	// at its value. Untyped constants take their default type.
	b := new(42)
	c := new(0.5)
	d := new("go1.26")
	e := new(int64(300)) // a conversion picks another type

	fmt.Printf("%T %v\n", a, *a)
	fmt.Printf("%T %v\n", b, *b)
	fmt.Printf("%T %v\n", c, *c)
	fmt.Printf("%T %v\n", d, *d)
	fmt.Printf("%T %v\n", e, *e)

	// Any expression works, including a call.
	f := new(len("hello") * 2)
	fmt.Println(*f)
}
