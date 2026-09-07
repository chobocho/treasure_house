// monitor — 시스템 모니터. 보리차로 만든 두 번째 응용 프로그램.
//
//	go run ./cmd/monitor
//	go run ./cmd/monitor -interval 200ms
package main

import (
	"flag"
	"fmt"
	"os"

	"treasure/boricha/apps/monitor"
	"treasure/boricha/tea"
)

func main() {
	iv := flag.Duration("interval", 0, "읽는 간격 (0이면 기본값)")
	flag.Parse()

	m := monitor.New()
	if *iv > 0 {
		m = m.SetInterval(*iv)
	}
	if _, err := tea.NewProgram(m, tea.WithAltScreen()).Run(); err != nil {
		fmt.Fprintln(os.Stderr, "오류:", err)
		os.Exit(1)
	}
}
