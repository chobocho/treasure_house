// 02_counter — 상태가 있는 첫 프로그램. 그리고 Bubble Tea 의 가장 중요한 규칙.
//
// 규칙: **모델은 값이다.** Update 는 모델의 복사본을 받는다.
// m.n++ 는 복사본을 늘릴 뿐이고, 늘어난 복사본을 return 해야 비로소 반영된다.
// 포인터 리시버(func (m *model) Update)를 쓰고 싶어지겠지만 참으라 —
// 값이라서 "이전 상태"가 저절로 보존되고, 그 덕에 테스트가 이렇게 쉬워진다.
//
//	go run ./examples/02_counter
package main

import (
	"fmt"
	"os"

	tea "charm.land/bubbletea/v2"
)

type model struct {
	n int
}

func (m model) Init() tea.Cmd { return nil }

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.KeyPressMsg:
		switch msg.String() {
		case "up", "k", "+":
			m.n++
		case "down", "j", "-":
			m.n--
		case "r":
			m.n = 0
		case "q", "ctrl+c", "esc":
			return m, tea.Quit
		}
	}
	// 여기서 돌려주는 m 은 위에서 고친 **복사본**이다.
	// 이 return 을 빠뜨리고 원본을 돌려주면 화면이 영원히 0 에 머문다.
	return m, nil
}

func (m model) View() tea.View {
	return tea.NewView(fmt.Sprintf(
		"세어 보자: %d\n\n↑/k/+ 올리기   ↓/j/- 내리기   r 되돌리기   q 끝내기\n",
		m.n))
}

func main() {
	if _, err := tea.NewProgram(model{}).Run(); err != nil {
		fmt.Fprintln(os.Stderr, "실행 실패:", err)
		os.Exit(1)
	}
}
