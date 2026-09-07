// 01_hello — 가장 작은 보리차 프로그램.
//
// 모델 하나에 메서드 셋. 이것이 전부다.
// 원시 모드도, 이스케이프 시퀀스도, 화면 지우기도 여기 없다 — 전부 tea 가 한다.
// 0단계의 examples/00_raw 와 견줘 보면 프레임워크가 무엇을 가져갔는지 한눈에 보인다.
package main

import (
	"fmt"
	"os"

	"treasure/boricha/tea"
)

// model 은 이 프로그램의 상태 전부다. 여기서는 담을 것이 없어 빈 구조체다.
type model struct{}

// Init 은 시작할 때 딱 한 번 불린다. 처음 할 일이 없으면 nil 을 돌려준다.
func (m model) Init() tea.Cmd { return nil }

// Update 는 사건 하나를 받아 새 모델과 다음에 할 일을 돌려준다.
func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	if key, ok := msg.(tea.KeyMsg); ok {
		switch key.String() {
		case "q", "ctrl+c", "esc":
			// tea.Quit 은 그 자체가 Cmd 다(func() Msg 꼴이라 그대로 넘길 수 있다).
			return m, tea.Quit
		}
	}
	return m, nil
}

// View 는 지금 상태를 화면 문자열로 그린다. 매 사건마다 불린다.
// 화면 전체를 매번 새로 만들지만, 실제로 터미널에 나가는 것은 달라진 줄뿐이다.
func (m model) View() string {
	return "안녕하세요, 보리차입니다 🍵\n\nq 또는 esc 로 끝냅니다."
}

func main() {
	if _, err := tea.NewProgram(model{}, tea.WithAltScreen()).Run(); err != nil {
		fmt.Fprintln(os.Stderr, "오류:", err)
		os.Exit(1)
	}
}
