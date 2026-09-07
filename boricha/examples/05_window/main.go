// 05_window — 창 크기.
//
// 크기는 입력 흐름으로 오지 않는다. 터미널이 바이트를 보내는 것이 아니라
// 커널이 SIGWINCH 신호를 보내고, tea 가 그것을 WindowSizeMsg 로 바꿔 준다.
// 시작할 때도 한 번 보내 주므로, 모델은 "크기를 아직 모르는 상태" 를 다룰 필요가 없다.
//
// 터미널 창을 마우스로 끌어 크기를 바꿔 보라.
package main

import (
	"fmt"
	"os"
	"strings"

	"treasure/boricha/tea"
	"treasure/boricha/width"
)

type model struct {
	w, h    int
	changes int
}

func (m model) Init() tea.Cmd { return nil }

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		m.w, m.h = msg.Width, msg.Height
		m.changes++
	case tea.KeyMsg:
		if s := msg.String(); s == "q" || s == "ctrl+c" {
			return m, tea.Quit
		}
	}
	return m, nil
}

// View 는 지금 크기에 꼭 맞는 상자를 그린다.
// 폭을 셀 때 width.StringWidth 를 쓰는 것이 핵심이다 — 안쪽 글에 한글이 섞이면
// len() 으로는 상자가 어긋난다.
func (m model) View() string {
	if m.w < 4 || m.h < 4 {
		return "창이 너무 작습니다"
	}
	inner := m.w - 2
	lines := []string{
		"",
		fmt.Sprintf("  %d칸 × %d줄", m.w, m.h),
		fmt.Sprintf("  크기 알림 %d번", m.changes),
		"",
		"  창을 끌어서 크기를 바꿔 보세요",
		"  q 로 끝냅니다",
	}
	var b strings.Builder
	b.WriteString("┌" + strings.Repeat("─", inner) + "┐\n")
	for i := 0; i < m.h-2; i++ {
		s := ""
		if i < len(lines) {
			s = lines[i]
		}
		b.WriteString("│" + width.Pad(width.Truncate(s, inner), inner) + "│")
		if i < m.h-3 {
			b.WriteString("\n")
		}
	}
	b.WriteString("\n└" + strings.Repeat("─", inner) + "┘")
	return b.String()
}

func main() {
	if _, err := tea.NewProgram(model{}, tea.WithAltScreen()).Run(); err != nil {
		fmt.Fprintln(os.Stderr, "오류:", err)
		os.Exit(1)
	}
}
