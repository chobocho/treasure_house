// 슬라이드 p3-v14-ptrptr — **T 에서 메서드 호출 금지, Go 1.4
package main

import "fmt"

type T int

func (T) M() { fmt.Println("M called") }

func main() {
	t := T(1)
	p := &t
	x := &p // x has type **T

	p.M()    // ok: one automatic dereference
	(*x).M() // ok: the fix is an explicit dereference
	x.M()    // gc and gccgo accepted this before Go 1.4
}
