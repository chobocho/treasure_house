// todo — 할 일 목록. 보리차로 만든 첫 번째 응용 프로그램.
//
//	go run ./cmd/todo                 ~/.boricha_todo.json 에 저장
//	go run ./cmd/todo -file /tmp/a.json
//	go run ./cmd/todo -file ""        저장하지 않음(기록·시험용)
package main

import (
	"flag"
	"fmt"
	"os"
	"path/filepath"

	"treasure/boricha/apps/todo"
	"treasure/boricha/tea"
)

func main() {
	def := ".boricha_todo.json"
	if home, err := os.UserHomeDir(); err == nil {
		def = filepath.Join(home, ".boricha_todo.json")
	}
	path := flag.String("file", def, "할 일을 저장할 파일 (빈 문자열이면 저장 안 함)")
	flag.Parse()

	p := tea.NewProgram(todo.New(*path), tea.WithAltScreen())
	if _, err := p.Run(); err != nil {
		fmt.Fprintln(os.Stderr, "오류:", err)
		os.Exit(1)
	}
}
