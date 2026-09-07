// 09_paste — 괄호 붙은 붙여넣기.
//
// 켜지 않으면 붙여넣기는 그냥 "키를 아주 빨리 여러 번 친 것" 으로 온다.
// 그래서 여러 줄을 붙여넣으면 줄바꿈이 전부 엔터로 들어가, 입력창이 제멋대로 확정된다.
// 켜면 터미널이 붙여넣기의 앞뒤를 표시해 주고, 우리는 그것을 PasteMsg 한 덩어리로 받는다.
//
// 여기서 무언가 복사해 붙여넣어 보라. 여러 줄이면 더 좋다.
package main

import (
	"fmt"
	"os"
	"strings"

	"treasure/boricha/tea"
)

type model struct {
	typed  []rune
	pastes []string
}

func (m model) Init() tea.Cmd { return nil }

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.KeyMsg:
		switch msg.String() {
		case "ctrl+c", "esc":
			return m, tea.Quit
		case "backspace":
			if len(m.typed) > 0 {
				m.typed = append([]rune{}, m.typed[:len(m.typed)-1]...)
			}
		default:
			// Text 가 비어 있지 않다는 것이 곧 "글자로 넣어도 되는 키" 라는 뜻이다.
			// 조합키(ctrl+a, alt+x)나 특수키는 Text 가 비어 있다.
			if msg.Text != "" {
				m.typed = append(append([]rune{}, m.typed...), []rune(msg.Text)...)
			}
		}
	case tea.PasteMsg:
		m.pastes = append(append([]string{}, m.pastes...), string(msg))
	}
	return m, nil
}

func (m model) View() string {
	var b strings.Builder
	b.WriteString("붙여넣기 실습 (esc 로 끝내기)\n")
	b.WriteString(strings.Repeat("─", 44) + "\n\n")
	b.WriteString("친 글자: " + string(m.typed) + "▏\n\n")
	b.WriteString(fmt.Sprintf("붙여넣기 %d번\n", len(m.pastes)))
	for i, p := range m.pastes {
		lines := strings.Split(p, "\n")
		b.WriteString(fmt.Sprintf("  %d. %d글자 · %d줄  %q\n",
			i+1, len([]rune(p)), len(lines), first(p, 30)))
	}
	return b.String()
}

func first(s string, n int) string {
	r := []rune(s)
	if len(r) <= n {
		return s
	}
	return string(r[:n]) + "…"
}

func main() {
	p := tea.NewProgram(model{}, tea.WithAltScreen(), tea.WithBracketedPaste())
	if _, err := p.Run(); err != nil {
		fmt.Fprintln(os.Stderr, "오류:", err)
		os.Exit(1)
	}
}
