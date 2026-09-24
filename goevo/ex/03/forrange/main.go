// 슬라이드 p3-v14-forrange — 변수 없는 for range x, Go 1.4
package main

import (
	"fmt"
	"go/ast"
	"go/parser"
)

func main() {
	ticks := make(chan int, 3)
	for i := 0; i < 3; i++ {
		ticks <- i
	}
	close(ticks)

	n := 0
	for _ = range ticks { // before Go 1.4: a variable was required
		n++
	}
	fmt.Println("drained", n)

	for range []string{"a", "b"} { // Go 1.4: no variable at all
		n++
	}
	fmt.Println("counted", n)

	// tools see it too: RangeStmt.Key is now nil
	fn, err := parser.ParseExpr("func() { for range x {} }")
	if err != nil {
		panic(err)
	}
	loop := fn.(*ast.FuncLit).Body.List[0].(*ast.RangeStmt)
	fmt.Println("Key == nil:", loop.Key == nil)
}
