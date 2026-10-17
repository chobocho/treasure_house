// Package sdksrc 는 설치된 a2a-go 소스를 찾아 읽는 9부 예제의 도우미다.
//
// 1장의 지도·이름 찾기와 2~4장의 API 목록이 모두 이 소스를 읽는다.
// 위치는 go 명령에 묻는다 — 모듈 캐시 경로는 기계마다 다르기 때문.
package sdksrc

import (
	"go/ast"
	"go/parser"
	"go/token"
	"os"
	"os/exec"
	"path/filepath"
	"slices"
	"strconv"
	"strings"
)

// Module 은 SDK 의 모듈 경로다.
const Module = "github.com/a2aproject/a2a-go/v2"

// Dir 는 설치본의 뿌리 디렉터리(모듈 캐시 안)다.
func Dir() string {
	out, err := exec.Command("go", "list", "-m", "-f", "{{.Dir}}",
		Module).Output()
	if err != nil {
		panic(err)
	}
	return strings.TrimSpace(string(out))
}

// Files 는 패키지 디렉터리(예: "a2asrv")의 시험 아닌 .go 파일을
// 이름 차례로 돌려준다.
func Files(root, pkg string) []string {
	names, _ := filepath.Glob(filepath.Join(root, pkg, "*.go"))
	var out []string
	for _, n := range names {
		if !strings.HasSuffix(n, "_test.go") {
			out = append(out, n)
		}
	}
	slices.Sort(out)
	return out
}

// Parse 는 패키지 하나를 주석까지 읽는다.
func Parse(root, pkg string) (*token.FileSet, []*ast.File) {
	fset := token.NewFileSet()
	var files []*ast.File
	for _, n := range Files(root, pkg) {
		f, err := parser.ParseFile(fset, n, nil, parser.ParseComments)
		if err != nil {
			panic(err)
		}
		files = append(files, f)
	}
	return fset, files
}

// Where 는 위치를 설치본 뿌리에서 본 "a2asrv/handler.go:184" 로 쓴다.
func Where(root string, fset *token.FileSet, p token.Pos) string {
	pos := fset.Position(p)
	rel, _ := filepath.Rel(root, pos.Filename)
	return filepath.ToSlash(rel) + ":" + strconv.Itoa(pos.Line)
}

// Lines 는 파일의 줄 수다.
func Lines(path string) int {
	b, err := os.ReadFile(path)
	if err != nil {
		panic(err)
	}
	return strings.Count(string(b), "\n")
}
