// 설치된 a2a-go 의 패키지 지도 — 패키지마다 파일·줄 수와 바깥 모듈.
//
//	go run ./09/sdk_map
package main

import (
	"fmt"
	"go/parser"
	"go/token"
	"io/fs"
	"os"
	"path/filepath"
	"slices"
	"strconv"
	"strings"

	"example.com/workshop/09/sdksrc"
)

// 라이브러리가 아닌 디렉터리(예제·시험·문서·도구)는 지도에서 뺀다.
var skip = []string{"docs", "e2e", "examples", "tools", "acts"}

// region: map
func main() {
	root := sdksrc.Dir()
	mods := requires(filepath.Join(root, "go.mod"))
	have := downloaded("go.sum") // 우리 모듈(ex/go)이 받은 것
	fmt.Println("패키지                          파일   줄 수  " +
		"바깥 모듈 (✗ = 우리 go.sum 에 없다)")
	var nPkg, nFile, nLine int
	for _, pkg := range packages(root) {
		files := sdksrc.Files(root, pkg)
		lines, ext := 0, map[string]bool{}
		for _, f := range files {
			lines += sdksrc.Lines(f)
			for _, m := range external(f, mods) {
				ext[m] = true
			}
		}
		var shown []string
		for _, m := range slices.Sorted(keys(ext)) {
			mark := ""
			if !have[m] {
				mark = "✗"
			}
			shown = append(shown, short(m)+mark)
		}
		row := fmt.Sprintf("%-31s %4d %7s  %s", pkg, len(files),
			comma(lines), strings.Join(shown, " "))
		fmt.Println(strings.TrimRight(row, " "))
		nPkg, nFile, nLine = nPkg+1, nFile+len(files), nLine+lines
	}
	fmt.Printf("합계 패키지 %d개, 파일 %d개, %s줄\n",
		nPkg, nFile, comma(nLine))
}

// endregion

// packages 는 시험 아닌 .go 파일이 있는 디렉터리 — 뿌리에서 본 경로.
func packages(root string) []string {
	var out []string
	walk := func(p string, d fs.DirEntry, _ error) error {
		if !d.IsDir() {
			return nil
		}
		rel, _ := filepath.Rel(root, p)
		top, _, _ := strings.Cut(filepath.ToSlash(rel), "/")
		hidden := strings.HasPrefix(d.Name(), ".") && rel != "."
		if hidden || slices.Contains(skip, top) ||
			d.Name() == "testdata" {
			return filepath.SkipDir
		}
		if rel != "." && len(sdksrc.Files(root, rel)) > 0 {
			out = append(out, filepath.ToSlash(rel))
		}
		return nil
	}
	filepath.WalkDir(root, walk)
	return out
}

// requires 는 SDK 의 go.mod 가 요구하는 모듈 경로들.
func requires(path string) []string {
	b, _ := os.ReadFile(path)
	var out []string
	for _, ln := range strings.Split(string(b), "\n") {
		f := strings.Fields(strings.TrimPrefix(ln, "require "))
		if len(f) >= 2 && strings.HasPrefix(f[1], "v") {
			out = append(out, f[0])
		}
	}
	return out
}

// downloaded 는 go.sum 에서 내용(h1, /go.mod 아닌 줄)이 있는 모듈.
func downloaded(path string) map[string]bool {
	b, _ := os.ReadFile(path)
	out := map[string]bool{}
	for _, ln := range strings.Split(string(b), "\n") {
		f := strings.Fields(ln)
		if len(f) == 3 && !strings.HasSuffix(f[1], "/go.mod") {
			out[f[0]] = true
		}
	}
	return out
}

// external 은 파일이 가져오는 바깥 모듈 — 가장 긴 접두어로 고른다.
func external(file string, mods []string) []string {
	f, err := parser.ParseFile(token.NewFileSet(), file, nil,
		parser.ImportsOnly)
	if err != nil {
		panic(err)
	}
	var out []string
	for _, im := range f.Imports {
		path, _ := strconv.Unquote(im.Path.Value)
		if strings.HasPrefix(path, sdksrc.Module) {
			continue // SDK 안의 다른 패키지
		}
		best := ""
		for _, m := range mods {
			if (path == m || strings.HasPrefix(path, m+"/")) &&
				len(m) > len(best) {
				best = m
			}
		}
		if best != "" {
			out = append(out, best)
		}
	}
	return out
}

// short 는 호스트를 뗀 모듈 이름(google.golang.org/grpc → grpc).
func short(m string) string {
	_, rest, _ := strings.Cut(m, "/")
	return strings.TrimPrefix(rest, "x/")
}

func keys(m map[string]bool) func(func(string) bool) {
	return func(yield func(string) bool) {
		for k := range m {
			if !yield(k) {
				return
			}
		}
	}
}

func comma(n int) string {
	s := strconv.Itoa(n)
	for i := len(s) - 3; i > 0; i -= 3 {
		s = s[:i] + "," + s[i:]
	}
	return s
}
