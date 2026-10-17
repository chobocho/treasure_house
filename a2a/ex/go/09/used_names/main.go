// 완성 에이전트(agents/)가 쓰는 SDK 이름 — 이름마다 몇 파일이 쓰나.
//
//	go run ./09/used_names
package main

import (
	"fmt"
	"go/ast"
	"go/parser"
	"go/token"
	"maps"
	"path"
	"path/filepath"
	"slices"
	"strconv"
	"strings"

	"example.com/workshop/09/sdksrc"
)

// region: used
func main() {
	files, _ := filepath.Glob("agents/*/*.go")
	used := map[string]map[string]int{} // 패키지 → 이름 → 파일 수
	for _, name := range files {
		f, err := parser.ParseFile(token.NewFileSet(), name, nil, 0)
		if err != nil {
			panic(err)
		}
		pkgOf := map[string]string{} // 파일 안의 이름 → SDK 패키지
		for _, im := range f.Imports {
			p, _ := strconv.Unquote(im.Path.Value)
			if rel, ok := strings.CutPrefix(p, sdksrc.Module+"/"); ok {
				pkgOf[path.Base(p)] = rel
			}
		}
		seen := map[string]bool{}
		ast.Inspect(f, func(n ast.Node) bool {
			s, ok := n.(*ast.SelectorExpr)
			if !ok {
				return true
			}
			if x, isID := s.X.(*ast.Ident); isID {
				pkg := pkgOf[x.Name]
				if pkg != "" && !seen[pkg+"."+s.Sel.Name] {
					seen[pkg+"."+s.Sel.Name] = true
					if used[pkg] == nil {
						used[pkg] = map[string]int{}
					}
					used[pkg][s.Sel.Name]++
				}
			}
			return true
		})
	}
	total := 0
	for _, pkg := range slices.Sorted(maps.Keys(used)) {
		fmt.Printf("%s (%d):\n", pkg, len(used[pkg]))
		line := "   "
		for _, n := range slices.Sorted(maps.Keys(used[pkg])) {
			item := fmt.Sprintf(" %s(%d)", n, used[pkg][n])
			if len(line)+len(item) > 72 {
				fmt.Println(line)
				line = "   "
			}
			line += item
		}
		fmt.Println(line)
		total += len(used[pkg])
	}
	fmt.Printf("이름 %d 개, 패키지 %d 개, 파일 %d 개\n",
		total, len(used), len(files))
}

// endregion
