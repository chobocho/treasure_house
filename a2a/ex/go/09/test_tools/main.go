// 시험 도구로 무엇이 있나 — 우리 모듈의 go.sum 과 표준 라이브러리.
//
//	go run ./09/test_tools
package main

import (
	"fmt"
	"go/ast"
	"go/parser"
	"go/token"
	"maps"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"slices"
	"strings"
)

func main() {
	fmt.Println("Go", runtime.Version())
	// region: sum
	// go.sum 의 모듈마다 받은 것이 소스(zip)인지 go.mod 뿐인지
	raw, _ := os.ReadFile("go.sum")
	full := map[string]bool{}
	for _, line := range strings.Split(string(raw), "\n") {
		f := strings.Fields(line)
		if len(f) == 3 {
			full[f[0]] = full[f[0]] ||
				!strings.HasSuffix(f[1], "/go.mod")
		}
	}
	for _, m := range slices.Sorted(maps.Keys(full)) {
		what := map[bool]string{true: "소스", false: "go.mod 뿐"}
		fmt.Printf("  %-32s %s\n", m, what[full[m]])
	}
	_, testify := full["github.com/stretchr/testify"]
	fmt.Println("  testify:", testify)
	// endregion
	httptest()
}

// httptest 는 표준 net/http/httptest 의 맨 윗단 함수를 찍는다.
func httptest() {
	out, _ := exec.Command("go", "env", "GOROOT").Output()
	dir := filepath.Join(strings.TrimSpace(string(out)),
		"src", "net", "http", "httptest")
	pkgs, _ := parser.ParseDir(token.NewFileSet(), dir,
		func(fi os.FileInfo) bool {
			return !strings.HasSuffix(fi.Name(), "_test.go")
		}, 0)
	var names []string
	for _, f := range pkgs["httptest"].Files {
		for _, d := range f.Decls {
			fn, ok := d.(*ast.FuncDecl)
			if ok && fn.Recv == nil && fn.Name.IsExported() {
				names = append(names, fn.Name.Name)
			}
		}
	}
	slices.Sort(names)
	fmt.Println("net/http/httptest:", strings.Join(names, " "))
}
