// 이 부에서 쓸 이름이 설치본의 어느 파일·몇째 줄에 있나.
//
//	go run ./09/where
package main

import (
	"fmt"
	"go/ast"
	"go/token"
	"strings"

	"example.com/workshop/09/sdksrc"
)

// region: where
// 패키지의 맨 윗단 선언(type·func·var·const)에서 이름을 찾는다.
// 메서드(받는 쪽이 있는 func)는 건너뛴다.
func where(root, pkg, name string) {
	fset, files := sdksrc.Parse(root, pkg)
	for _, f := range files {
		for _, d := range f.Decls {
			kind, pos := find(d, name)
			if kind != "" {
				full := pkg[strings.LastIndex(pkg, "/")+1:] + "." + name
				fmt.Printf("%-33s %-5s %s\n", full, kind,
					sdksrc.Where(root, fset, pos))
				return
			}
		}
	}
	fmt.Printf("%s.%s 못 찾음\n", pkg, name)
}

// endregion

func find(d ast.Decl, name string) (string, token.Pos) {
	switch d := d.(type) {
	case *ast.FuncDecl:
		if d.Recv == nil && d.Name.Name == name {
			return "func", d.Pos()
		}
	case *ast.GenDecl:
		for _, s := range d.Specs {
			switch s := s.(type) {
			case *ast.TypeSpec:
				if s.Name.Name == name {
					return "type", s.Pos()
				}
			case *ast.ValueSpec:
				for _, n := range s.Names {
					if n.Name == name {
						return d.Tok.String(), n.Pos()
					}
				}
			}
		}
	}
	return "", token.NoPos
}

func main() {
	root := sdksrc.Dir()
	for _, q := range [][2]string{
		{"a2a", "Part"}, {"a2a", "TaskState"}, {"a2a", "Event"},
		{"a2a", "NewStatusUpdateEvent"},
		{"a2asrv", "AgentExecutor"}, {"a2asrv", "ExecutorContext"},
		{"a2asrv", "NewHandler"}, {"a2asrv", "RequestHandler"},
		{"a2asrv/taskstore", "NewInMemory"},
		{"a2asrv", "NewJSONRPCHandler"},
		{"a2asrv", "NewStaticAgentCardHandler"},
		{"a2asrv", "CallContext"},
	} {
		where(root, q[0], q[1])
	}
}
