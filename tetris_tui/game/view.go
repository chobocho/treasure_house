package game

import (
	"fmt"

	tea "charm.land/bubbletea/v2"
	"charm.land/lipgloss/v2"

	"treasure/tetris_tui/core"
	"treasure/tetris_tui/ui"
)

// View 는 판과 패널을 나란히 놓고 그 아래에 도움말을 깐다.
//
// 세 가지 상태를 그린다:
//  1. 아직 창 크기를 모름 — 첫 WindowSizeMsg 전의 한 프레임
//  2. 창이 너무 작음 — 지금 크기와 필요한 크기를 함께 알려 준다
//  3. 정상
//
// 1번을 빼먹으면 첫 프레임에서 0 폭으로 계산하다 죽는다(05_window 의 교훈).
func (m Model) View() tea.View {
	minW, minH := ui.MinSize(1)

	if m.w == 0 || m.h == 0 {
		return tea.NewView("창 크기를 기다리는 중…\n")
	}
	if m.w < minW || m.h < minH {
		msg := fmt.Sprintf("터미널을 키워 주세요\n\n지금 %d×%d · 필요 %d×%d", m.w, m.h, minW, minH)
		v := tea.NewView(lipgloss.Place(m.w, m.h, lipgloss.Center, lipgloss.Center, msg))
		v.AltScreen = true
		return v
	}

	s := m.g.Stats()
	board := ui.RenderBoard(m.g.Cells(), m.g.Overlay(), "1인용", s.State == core.StateOver)
	panel := ui.RenderPanel(s, m.g.Next(3), "")

	body := lipgloss.JoinHorizontal(lipgloss.Top, board, panel)

	// 도움말은 창보다 길 수 있다. 줄바꿈하면 높이가 늘어 판이 밀리므로 잘라 낸다 —
	// 좁은 터미널에서는 뒷부분이 안 보이는 편이 판이 어긋나는 것보다 낫다.
	help := lipgloss.NewStyle().MaxWidth(m.w).Render(m.helpText())
	out := lipgloss.JoinVertical(lipgloss.Left, body, help)

	// Place 로 창 전체를 채운다. 화면이 창보다 작으면 이전 프레임의 찌꺼기가 남고,
	// 크면 터미널이 스크롤되면서 위쪽이 잘려 나간다.
	// MaxWidth/MaxHeight 는 마지막 안전장치다 — 어디선가 한 칸이 새도 여기서 막힌다.
	out = lipgloss.NewStyle().MaxWidth(m.w).MaxHeight(m.h).Render(out)
	v := tea.NewView(lipgloss.Place(m.w, m.h, lipgloss.Left, lipgloss.Top, out))
	v.AltScreen = true
	return v
}

// helpText 는 아래쪽 한 줄. F1 을 누르면 조작표 전체로 바뀐다.
//
// 문구를 손으로 적지 않고 ui 의 키맵에서 뽑는다 —
// 배치를 바꿨는데 도움말이 그대로면 사용자만 거짓말을 읽게 된다.
func (m Model) helpText() string {
	if m.help {
		return ui.DimStyle.Render(m.keys.HelpLine() + "\n" + ui.GlobalHelpLine())
	}
	return ui.DimStyle.Render("F1 조작법 · " + ui.GlobalHelpLine())
}
