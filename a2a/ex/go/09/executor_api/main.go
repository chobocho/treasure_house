// 설치본에서 실행기 쪽 선언을 주석 없이 찍는다.
//
//	go run ./09/executor_api
package main

import (
	"fmt"
	"go/ast"
	"go/printer"
	"go/token"
	"os"
	"slices"

	"example.com/workshop/09/sdksrc"
)

// region: api
func main() {
	root := sdksrc.Dir()
	fset, files := sdksrc.Parse(root, "a2asrv")
	want := []string{"AgentExecutor", "AgentExecutorFunc",
		"AgentExecutionCleaner"}
	for _, f := range files {
		for _, d := range f.Decls {
			g, ok := d.(*ast.GenDecl)
			if !ok || g.Tok != token.TYPE {
				continue
			}
			for _, s := range g.Specs {
				ts := s.(*ast.TypeSpec)
				if !slices.Contains(want, ts.Name.Name) {
					continue
				}
				// 메서드에 붙은 문서 주석을 떼고 찍는다
				ast.Inspect(ts, func(n ast.Node) bool {
					if f, ok := n.(*ast.Field); ok {
						f.Doc, f.Comment = nil, nil
					}
					return true
				})
				fmt.Printf("// %s\ntype ",
					sdksrc.Where(root, fset, ts.Pos()))
				printer.Fprint(os.Stdout, fset, ts)
				fmt.Println()
			}
		}
	}
}

// endregion
