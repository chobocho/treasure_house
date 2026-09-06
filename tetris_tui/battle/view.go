package battle

import (
	"fmt"

	tea "charm.land/bubbletea/v2"
	"charm.land/lipgloss/v2"

	"treasure/tetris_tui/core"
	"treasure/tetris_tui/ui"
)

// View 는 두 판을 바깥에, 패널 둘을 가운데에 놓는다.
//
//	[판 왼쪽][패널 왼쪽][패널 오른쪽][판 오른쪽]
//	  22        14         14         22      = 72칸
//
// 대전 화면의 관례다. 판이 바깥에 있어야 두 사람이 각자의 쪽을 보기 쉽고,
// 숫자가 가운데 모여 있어야 "누가 이기고 있나"를 한눈에 본다.
func (m Model) View() tea.View {
	minW, minH := ui.MinSize(Seats)

	if m.w == 0 || m.h == 0 {
		return tea.NewView("창 크기를 기다리는 중…\n")
	}
	if m.w < minW || m.h < minH {
		msg := fmt.Sprintf("터미널을 키워 주세요\n\n지금 %d×%d · 필요 %d×%d", m.w, m.h, minW, minH)
		v := tea.NewView(lipgloss.Place(m.w, m.h, lipgloss.Center, lipgloss.Center, msg))
		v.AltScreen = true
		return v
	}

	parts := make([]string, 0, 4)
	for _, s := range []Seat{Left, Right} {
		g := m.match.Game(s)
		st := g.Stats()
		board := ui.RenderBoard(g.Cells(), g.Overlay(), m.names[s], st.State == core.StateOver)
		panel := ui.RenderPanel(m.seatTitle(s), st, g.Next(3), m.seatNote(s))
		if s == Left {
			parts = append(parts, board, panel)
			continue
		}
		parts = append(parts, panel, board)
	}

	body := lipgloss.JoinHorizontal(lipgloss.Top, parts...)
	help := lipgloss.NewStyle().MaxWidth(m.w).Render(m.helpText())
	out := lipgloss.JoinVertical(lipgloss.Left, body, help)
	out = lipgloss.NewStyle().MaxWidth(m.w).MaxHeight(m.h).Render(out)

	v := tea.NewView(lipgloss.Place(m.w, m.h, lipgloss.Left, lipgloss.Top, out))
	v.AltScreen = true
	return v
}

// seatNote 는 패널 아래에 붙는 몇 줄 — 승수, 보낸 줄 수, AI 의 상태.
//
// 줄 수가 자리마다 달라지지 않게 "생각 중" 자리는 늘 한 줄을 차지한다.
// 그러지 않으면 AI 가 생각을 시작할 때마다 패널이 한 줄씩 늘었다 줄었다 한다.
func (m Model) seatNote(s Seat) string {
	note := fmt.Sprintf("승 %d\n보냄 %d\n", m.match.Wins(s), m.match.Sent(s))
	if d := m.drv[s]; d != nil && d.Thinking() {
		return note + "생각 중…"
	}
	return note + " "
}

// helpText 는 아래쪽 한 줄. 라운드가 끝나면 결과와 다음 안내로 바뀐다.
func (m Model) helpText() string {
	if w, draw, over := m.match.RoundOver(); over {
		result := m.names[w] + " 승!"
		if draw {
			result = "무승부"
		}
		if champ, done := m.match.MatchOver(); done {
			return ui.OverStyle.Render(
				fmt.Sprintf("%s  —  %s 가 %d판 %d선승제를 가져갔다. Enter 새 대전 · Esc 나가기",
					result, m.names[champ], m.match.BestOf(), m.match.BestOf()/2+1))
		}
		return ui.OverStyle.Render(result + "  —  Enter 다음 라운드 · r 처음부터 · Esc 나가기")
	}

	head := fmt.Sprintf("%d라운드 %d:%d · ",
		m.match.Round(), m.match.Wins(Left), m.match.Wins(Right))
	if m.help {
		return ui.DimStyle.Render(head + m.keyHelp())
	}
	// 기본 도움말은 짧게. 80칸 터미널에서 잘리지 않아야 한다.
	// 난이도는 판 제목과 패널에 이미 있으므로 여기서 또 적지 않는다 —
	// 한 줄이 잘리면 "Esc 나" 처럼 끝이 사라져서 안내가 아니라 소음이 된다.
	return ui.DimStyle.Render(head + "F1 조작법 · p 일시정지 · r 처음부터 · Esc 나가기")
}

// keyHelp 는 사람 자리의 조작표. 두 사람이면 둘 다 보여 준다.
// AI 자리가 있으면 난이도 전체 이름도 여기서 알려 준다.
func (m Model) keyHelp() string {
	out := ""
	if m.mode != Local2P {
		out = "AI " + m.level.Label
	}
	for s := Seat(0); s < Seats; s++ {
		if !m.human[s] {
			continue
		}
		if out != "" {
			out += "\n"
		}
		out += m.names[s] + ": " + m.keys[s].HelpLine()
	}
	if out != "" {
		out += "\n"
	}
	return out + ui.GlobalHelpLine()
}
