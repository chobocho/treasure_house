// v0.3 호환 패키지 a2acompat/a2av0 를 소스로 읽는다 — 우리 모듈은
// 그것이 가져오는 옛 모듈을 받지 않아 돌려 볼 수는 없다(1장).
//
//	go run ./09/compat_src
package main

import (
	"fmt"
	"go/ast"
	"path/filepath"
	"strconv"
	"strings"

	"example.com/workshop/09/sdksrc"
)

// region: list
func main() {
	root := sdksrc.Dir()
	fset, files := sdksrc.Parse(root, "a2acompat/a2av0")
	fmt.Println("a2acompat/a2av0 — 파일, 줄, 옛 모듈?, 공개 함수")
	conv := 0
	for _, f := range files {
		name := filepath.Base(fset.Position(f.Pos()).Filename)
		old := "  "
		for _, im := range f.Imports {
			p, _ := strconv.Unquote(im.Path.Value)
			if strings.HasPrefix(p, "github.com/a2aproject/a2a-go/") &&
				!strings.HasPrefix(p, sdksrc.Module) {
				old = "옛"
			}
		}
		var fns []string
		for _, n := range funcs(f) {
			if strings.HasPrefix(n, "ToV1") ||
				strings.HasPrefix(n, "FromV1") {
				conv++ // 타입 옮기기는 세기만 한다
				continue
			}
			fns = append(fns, n)
		}
		lines := sdksrc.Lines(fset.Position(f.Pos()).Filename)
		fmt.Printf("  %-18s %4d %s %s\n", name, lines, old,
			strings.Join(fns, " "))
	}
	fmt.Printf("  ToV1…·FromV1… 옮기기 함수 %d개\n", conv)
}

// endregion

// funcs 는 파일의 공개 함수(메서드 빼고) 이름을 차례대로 돌려준다.
func funcs(f *ast.File) []string {
	var out []string
	for _, d := range f.Decls {
		fn, ok := d.(*ast.FuncDecl)
		if ok && fn.Recv == nil && fn.Name.IsExported() {
			out = append(out, fn.Name.Name)
		}
	}
	return out
}
