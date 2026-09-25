// 슬라이드 p7-v123-gotypesalias — go/types 의 Alias, Go 1.23
package main

import (
	"fmt"
	"go/ast"
	"go/importer"
	"go/parser"
	"go/token"
	"go/types"
)

const src = `package p

type Celsius = float64

var T Celsius`

func main() {
	fset := token.NewFileSet()
	f, _ := parser.ParseFile(fset, "p.go", src, 0)
	conf := types.Config{Importer: importer.Default()}
	pkg, err := conf.Check("p", fset, []*ast.File{f}, nil)
	if err != nil {
		panic(err)
	}
	t := pkg.Scope().Lookup("T").Type()
	fmt.Printf("%v  %T\n", t, t) // the alias name survives
	fmt.Println(types.Unalias(t))
}
