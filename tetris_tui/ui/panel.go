package ui

import (
	"fmt"
	"strings"

	"charm.land/lipgloss/v2"

	"treasure/tetris_tui/core"
)

// PanelWidth 는 옆 패널의 폭(테두리 포함). 판과 마찬가지로 고정이다.
const PanelWidth = 14

// nextPreview 는 패널에 보여 주는 다음 조각의 개수.
// 셋이 관례다 — 하나면 계획을 못 세우고, 다섯이면 패널이 판보다 길어진다.
const nextPreview = 3

// RenderPanel 은 다음 조각·홀드·점수 패널을 그린다.
//
// 폭과 높이가 **언제나 같아야** 한다. 점수가 여섯 자리가 되거나 홀드가 비었다고
// 패널의 크기가 변하면, 옆에 붙어 있는 판이 매 프레임 좌우로 흔들린다.
// 그래서 값이 없는 자리도 "-" 로 채우고, 미리보기는 늘 같은 개수를 그린다.
func RenderPanel(s core.Stats, next []int, help string) string {
	lines := make([]string, 0, 20)

	lines = append(lines, LabelStyle.Render("다음"))
	for i := 0; i < nextPreview; i++ {
		p := -1
		if i < len(next) {
			p = next[i]
		}
		lines = append(lines, strings.Split(MiniPiece(p), "\n")...)
	}

	lines = append(lines, LabelStyle.Render("홀드"))
	lines = append(lines, strings.Split(MiniPiece(int(s.Hold)), "\n")...)

	lines = append(lines,
		LabelStyle.Render("점수"),
		ValueStyle.Render(fmt.Sprintf("%d", s.Score)),
		LabelStyle.Render("레벨 ")+ValueStyle.Render(fmt.Sprintf("%d", s.Level)),
		LabelStyle.Render("줄   ")+ValueStyle.Render(fmt.Sprintf("%d", s.Lines)),
		LabelStyle.Render("콤보 ")+ValueStyle.Render(comboText(s)),
		LabelStyle.Render("대기 ")+ValueStyle.Render(fmt.Sprintf("%d", s.Pending)),
	)

	if s.State == core.StateOver {
		lines = append(lines, "", OverStyle.Render("게임 오버"))
	} else if s.State == core.StatePause {
		lines = append(lines, "", TitleStyle.Render("일시정지"))
	}

	if help != "" {
		lines = append(lines, "", DimStyle.Render(help))
	}

	// Width 는 테두리를 **포함한** 폭이다. Width(PanelWidth-2) 로 쓰면
	// 완성품이 두 칸 좁아져서 옆의 판이 두 칸 밀린다 — 실제로 밟은 함정이다.
	body := lipgloss.JoinVertical(lipgloss.Left, lines...)
	return lipgloss.NewStyle().
		Border(lipgloss.RoundedBorder()).
		BorderForeground(lipgloss.Color(CellColors[8])).
		Width(PanelWidth).
		Render(body)
}

// comboText 는 콤보를 사람이 읽는 값으로 바꾼다.
// 코어의 콤보는 -1 이 "콤보 없음", 0 이 "첫 클리어"라 그대로 보여 주면 헷갈린다.
func comboText(s core.Stats) string {
	if s.Combo <= 0 {
		return "-"
	}
	return fmt.Sprintf("%d", s.Combo+1)
}
