// RequestHandler 의 메서드 ↔ A2A 메서드, 그리고 NewHandler 의 옵션.
//
//	go run ./09/handler_api
package main

import (
	"fmt"
	"go/ast"
	"go/types"
	"regexp"
	"strings"

	"example.com/workshop/09/sdksrc"
)

func main() {
	root := sdksrc.Dir()
	_, files := sdksrc.Parse(root, "a2asrv")
	// region: methods
	// 인터페이스 메서드마다 문서 주석이 맡은 A2A 메서드를 적었다
	// ("GetTask handles the 'GetTask' protocol method.")
	quoted := regexp.MustCompile("['`](\\w+)['`]")
	fmt.Println("RequestHandler 메서드 ← A2A 메서드 (handler.go)")
	for _, f := range files {
		ast.Inspect(f, func(n ast.Node) bool {
			ts, ok := n.(*ast.TypeSpec)
			if !ok || ts.Name.Name != "RequestHandler" {
				return true
			}
			iface := ts.Type.(*ast.InterfaceType)
			for _, m := range iface.Methods.List {
				a2a := quoted.FindStringSubmatch(m.Doc.Text())
				fmt.Printf("  %-22s ← %s\n", m.Names[0].Name, a2a[1])
			}
			return false
		})
	}
	// endregion
	// region: options
	// RequestHandlerOption 을 돌려주는 함수 — NewHandler 의 옵션들
	fmt.Println("a2asrv.NewHandler(executor, 옵션...) 의 옵션")
	for _, f := range files {
		for _, d := range f.Decls {
			fn, ok := d.(*ast.FuncDecl)
			if !ok || fn.Recv != nil || fn.Type.Results == nil {
				continue
			}
			res := fn.Type.Results.List[0].Type
			if id, ok := res.(*ast.Ident); !ok ||
				id.Name != "RequestHandlerOption" {
				continue
			}
			var ps []string
			for _, p := range fn.Type.Params.List {
				ps = append(ps, types.ExprString(p.Type))
			}
			args := strings.Join(ps, ", ")
			fmt.Printf("  %s(%s)\n", fn.Name.Name, args)
		}
	}
	// endregion
}
