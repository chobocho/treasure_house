// 슬라이드 p8-v125-goast — go/ast.PreorderStack·types.Var.Kind, Go 1.25
package main

import (
	"fmt"
	"go/ast"
	"go/parser"
	"go/token"
	"go/types"
	"strings"
)

const src = `package p
type T struct{ F int }
var G int
func (r T) M(a int) (b int) { c := a; return c + r.F }`

func main() {
	fset := token.NewFileSet()
	f, _ := parser.ParseFile(fset, "p.go", src, 0)

	// PreorderStack: like Inspect, plus the stack of enclosing nodes.
	ast.PreorderStack(f, nil, func(n ast.Node, stack []ast.Node) bool {
		if id, ok := n.(*ast.Ident); ok && id.Name == "c" {
			var path []string
			for _, s := range stack {
				t := fmt.Sprintf("%T", s)
				path = append(path, strings.TrimPrefix(t, "*ast."))
			}
			fmt.Println("c in", strings.Join(path, " > "))
		}
		return true
	})

	// Var.Kind: what sort of variable each object is.
	info := &types.Info{Defs: map[*ast.Ident]types.Object{}}
	new(types.Config).Check("p", fset, []*ast.File{f}, info)
	for _, name := range []string{"F", "G", "r", "a", "b", "c"} {
		for id, obj := range info.Defs {
			if v, ok := obj.(*types.Var); ok && id.Name == name {
				fmt.Printf("%s: %v\n", name, v.Kind())
			}
		}
	}
}
