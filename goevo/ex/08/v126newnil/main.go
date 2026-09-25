// 슬라이드 p8-v126-newtrap — new 에 넣을 수 없는 식, Go 1.26
package main

import "fmt"

func main() {
	p := new(nil)       // untyped nil has no type
	q := new(1 << 70)   // the default type int overflows
	r := new(fmt.Print) // fine: a func value
	fmt.Println(p, q, r != nil)
}
