// 05_window — 창 크기에 반응하기.
//
//	go run ./examples/05_window
//
// 터미널의 크기는 사용자가 언제든 바꾼다. Bubble Tea 는 시작할 때 한 번,
// 그리고 창이 바뀔 때마다 tea.WindowSizeMsg 를 보낸다.
//
// 두 가지를 배운다:
//
//  1. 첫 WindowSizeMsg 가 오기 **전에도** View 가 불린다. 그때 w=h=0 이다.
//     0 으로 뺄셈을 해서 음수 폭을 만들면 lipgloss 가 그 자리에서 죽는다.
//
//  2. 좁으면 "좁다"고 말해 준다. 테트리스 2인용은 72×24 가 필요한데,
//     그냥 깨진 화면을 보여 주는 것보다 이유를 알려 주는 편이 백 배 낫다.
package main

import (
	"fmt"
	"os"

	tea "charm.land/bubbletea/v2"

	"charm.land/lipgloss/v2"
)

// 이 예제가 요구하는 최소 크기. 진짜 게임 화면은 이 값을 손으로 적지 않고
// 판과 패널의 폭에서 계산한다(ui.MinSize) — 1인용 36×24, 2인용 72×24.
const (
	minW = 40
	minH = 12
)

type model struct {
	w, h int
}

func (m model) Init() tea.Cmd { return nil }

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		m.w, m.h = msg.Width, msg.Height
	case tea.KeyPressMsg:
		switch msg.String() {
		case "q", "ctrl+c", "esc":
			return m, tea.Quit
		}
	}
	return m, nil
}

func (m model) View() tea.View {
	// 아직 크기를 모른다 — 첫 WindowSizeMsg 가 오기 전의 한 프레임.
	// 여기서 Place(0, 0, ...) 를 부르면 안 된다.
	if m.w == 0 || m.h == 0 {
		return tea.NewView("창 크기를 기다리는 중…\n")
	}

	if m.w < minW || m.h < minH {
		msg := fmt.Sprintf("터미널을 키워 주세요\n\n지금 %d×%d · 필요 %d×%d",
			m.w, m.h, minW, minH)
		return tea.NewView(lipgloss.Place(m.w, m.h, lipgloss.Center, lipgloss.Center, msg))
	}

	box := lipgloss.NewStyle().
		Border(lipgloss.RoundedBorder()).
		Padding(1, 3).
		Render(fmt.Sprintf("창 크기: %d×%d\n\n창을 늘렸다 줄여 보세요.\nq 로 끝냅니다.", m.w, m.h))

	// Place 는 주어진 폭·높이 안에서 내용을 원하는 위치에 놓고 나머지를 공백으로 채운다.
	// 결과의 크기가 창과 정확히 같아야 터미널이 스크롤되지 않는다.
	return tea.NewView(lipgloss.Place(m.w, m.h, lipgloss.Center, lipgloss.Center, box))
}

func main() {
	if _, err := tea.NewProgram(model{}).Run(); err != nil {
		fmt.Fprintln(os.Stderr, "실행 실패:", err)
		os.Exit(1)
	}
}
