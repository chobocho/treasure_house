// a2a 패키지가 내보내는 이름을 종류별로 — 그리고 문자열 enum.
//
//	go run ./09/types_list
package main

import (
	"encoding/json"
	"fmt"
	"go/ast"
	"strconv"

	"github.com/a2aproject/a2a-go/v2/a2a"

	"example.com/workshop/09/sdksrc"
)

// region: kinds
// 맨 윗단 선언의 이름을 종류로 나눈다(메서드는 뺀다).
func kinds() map[string][]string {
	_, files := sdksrc.Parse(sdksrc.Dir(), "a2a")
	out := map[string][]string{}
	for _, f := range files {
		for _, d := range f.Decls {
			if fn, ok := d.(*ast.FuncDecl); ok && fn.Recv == nil {
				out["func"] = append(out["func"], fn.Name.Name)
			}
			g, ok := d.(*ast.GenDecl)
			if !ok {
				continue
			}
			for _, s := range g.Specs {
				switch s := s.(type) {
				case *ast.TypeSpec:
					k := typeKind(s.Type)
					out[k] = append(out[k], s.Name.Name)
				case *ast.ValueSpec:
					k := g.Tok.String() // var 또는 const
					for _, n := range s.Names {
						out[k] = append(out[k], n.Name)
					}
				}
			}
		}
	}
	return out
}

// endregion

func typeKind(t ast.Expr) string {
	switch t := t.(type) {
	case *ast.StructType:
		return "struct"
	case *ast.InterfaceType:
		return "interface"
	case *ast.Ident:
		if t.Name == "string" {
			return "string 바탕" // type TaskState string 같은 것
		}
	}
	return "별칭·기타" // []*Part, map, = PushConfig …
}

func main() {
	k := kinds()
	for _, kind := range []string{"struct", "interface",
		"string 바탕", "별칭·기타", "func", "var", "const"} {
		var pub []string
		for _, n := range k[kind] {
			if ast.IsExported(n) {
				pub = append(pub, n)
			}
		}
		fmt.Printf("%s %d개\n", kind, len(pub))
		if kind == "string 바탕" || kind == "interface" {
			wrap(pub)
		}
	}
	enums()
}

// wrap 은 이름들을 72칸 안에서 줄을 바꿔 찍는다.
func wrap(names []string) {
	line := "   "
	for _, n := range names {
		if len(line)+len(n)+1 > 72 {
			fmt.Println(line)
			line = "   "
		}
		line += " " + n
	}
	fmt.Println(line)
}

// pad 는 빈칸 n 개 — 한글 머리글은 %-28s 로는 칸이 안 맞는다.
func pad(n int) string { return fmt.Sprintf("%*s", n, "") }

// region: enums
func enums() {
	states := []a2a.TaskState{
		a2a.TaskStateUnspecified, a2a.TaskStateSubmitted,
		a2a.TaskStateWorking, a2a.TaskStateInputRequired,
		a2a.TaskStateAuthRequired, a2a.TaskStateCompleted,
		a2a.TaskStateCanceled, a2a.TaskStateFailed,
		a2a.TaskStateRejected,
	}
	fmt.Println("Go 값" + pad(24) + "와이어" + pad(23) + "Terminal()")
	for _, s := range states {
		wire, _ := json.Marshal(s)
		fmt.Printf("%-28s %-28s %v\n", strconv.Quote(string(s)),
			wire, s.Terminal())
	}
	var r a2a.MessageRole
	err := json.Unmarshal([]byte(`"user"`), &r) // v0.3 의 이름
	fmt.Printf("역할 \"user\" → %q, 오류 %v\n", string(r), err)
}

// endregion
