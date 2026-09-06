// 06_lipgloss — 화면을 꾸미는 층.
//
//	go run ./examples/06_lipgloss
//
// Bubble Tea 는 "무엇을 그릴지"만 정한다. "어떻게 보일지"는 Lip Gloss 의 일이다.
// 두 라이브러리는 문자열 하나로만 연결된다 — View 가 돌려주는 그 문자열이다.
//
// Lip Gloss 의 두 가지 성질을 몸에 익힌다:
//
//  1. Style 은 **값**이다. 메서드는 새 Style 을 돌려주고 원본은 그대로다.
//     (Bubble Tea 모델과 같은 규칙 — 이 라이브러리 묶음의 일관된 태도다)
//
//  2. 폭은 글자 수가 아니라 **칸 수**다. 한글 한 글자는 두 칸을 먹는다.
//     그래서 이 덱은 블록 한 칸을 두 글자(██)로 그린다 — 판이 정사각형이 된다.
package main

import (
	"fmt"
	"os"

	tea "charm.land/bubbletea/v2"

	"charm.land/lipgloss/v2"
)

// 블록 한 칸. 두 칸짜리 반각 문자 둘이라 폭이 정확히 2 다.
// (한글이나 이모지를 쓰면 폰트에 따라 폭이 흔들려 판이 어긋난다)
const cell = "██"

type model struct {
	w, h   int
	border bool
}

func (m model) Init() tea.Cmd { return nil }

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		m.w, m.h = msg.Width, msg.Height
		m.border = true // 첫 크기를 받을 때 테두리를 켜 둔다
	case tea.KeyPressMsg:
		switch msg.String() {
		case "b":
			m.border = !m.border
		case "q", "ctrl+c", "esc":
			return m, tea.Quit
		}
	}
	return m, nil
}

// 스타일들은 패키지 변수로 한 번만 만든다.
// View 에서 매번 NewStyle() 을 부르면 초당 수십 번 같은 구조체를 새로 짓게 된다.
var (
	titleStyle = lipgloss.NewStyle().
			Bold(true).
			Foreground(lipgloss.Color("#f7f")).
			Padding(0, 1)

	panelStyle = lipgloss.NewStyle().
			Width(18).
			Padding(0, 1)

	dimStyle = lipgloss.NewStyle().Foreground(lipgloss.Color("240"))
)

func (m model) View() tea.View {
	title := titleStyle.Render("제목 — Lip Gloss 맛보기")

	left := panelStyle.Render("왼쪽 패널\n\n" + cell + cell + cell + "\n" + cell + "  " + cell)
	right := panelStyle.Render("오른쪽 패널\n\n폭을 18칸으로\n고정했으므로\n두 패널의 폭이\n정확히 같다.")

	// 테두리는 폭과 높이를 각각 2 씩 늘린다. 레이아웃 계산에서 가장 자주 잊는 부분이다.
	box := lipgloss.NewStyle().Padding(0, 1)
	if m.border {
		box = box.Border(lipgloss.RoundedBorder()).BorderForeground(lipgloss.Color("63"))
	}

	// JoinHorizontal 은 높이가 다른 덩어리를 나란히 붙이고 짧은 쪽을 공백으로 채운다.
	// 첫 인자는 세로 정렬 기준 — Top 이면 위를 맞춘다.
	body := lipgloss.JoinHorizontal(lipgloss.Top, box.Render(left), box.Render(right))

	help := dimStyle.Render(fmt.Sprintf("b 테두리 %s · q 끝내기 · 창 %d×%d",
		onOff(m.border), m.w, m.h))

	return tea.NewView(lipgloss.JoinVertical(lipgloss.Left, title, body, help))
}

func onOff(b bool) string {
	if b {
		return "끄기"
	}
	return "켜기"
}

func main() {
	if _, err := tea.NewProgram(model{border: true}).Run(); err != nil {
		fmt.Fprintln(os.Stderr, "실행 실패:", err)
		os.Exit(1)
	}
}
