// 02_counter — 상태를 가진 모델.
//
// 새로 배우는 것 하나: **Update 는 고친 복사본을 돌려준다.**
// m.n++ 만 하고 원래 모델을 돌려주면 그 변경은 사라진다.
// 값 수신자(m model)라서 m 은 복사본이고, 돌려주지 않으면 버려지기 때문이다.
package main

import (
	"fmt"
	"os"

	"treasure/boricha/tea"
)

type model struct{ n int }

func (m model) Init() tea.Cmd { return nil }

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	key, ok := msg.(tea.KeyMsg)
	if !ok {
		return m, nil
	}
	switch key.String() {
	case "q", "ctrl+c":
		return m, tea.Quit
	case "up", "k", "+":
		m.n++
	case "down", "j", "-":
		m.n--
	case "r":
		m.n = 0
	}
	return m, nil // ← 고친 m 을 돌려준다. 이 한 글자가 이 예제의 전부다.
}

func (m model) View() string {
	return fmt.Sprintf("셈: %d\n\n↑/k/+ 늘리기   ↓/j/- 줄이기   r 되돌리기   q 끝내기", m.n)
}

func main() {
	if _, err := tea.NewProgram(model{}, tea.WithAltScreen()).Run(); err != nil {
		fmt.Fprintln(os.Stderr, "오류:", err)
		os.Exit(1)
	}
}
