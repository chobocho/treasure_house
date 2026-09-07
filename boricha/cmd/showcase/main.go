// showcase — 보리차가 할 수 있는 것을 한자리에 모은 전시장.
//
//	go run ./cmd/showcase
package main

import (
	"fmt"
	"os"

	"treasure/boricha/apps/showcase"
	"treasure/boricha/tea"
)

func main() {
	p := tea.NewProgram(showcase.New(),
		tea.WithAltScreen(), tea.WithMouse(), tea.WithBracketedPaste())
	if _, err := p.Run(); err != nil {
		fmt.Fprintln(os.Stderr, "오류:", err)
		os.Exit(1)
	}
}
