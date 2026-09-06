package ui

import "charm.land/lipgloss/v2"

// 조각 색. 인덱스는 코어의 칸 값 그대로다 — 0 = 빈칸, 1~7 = 조각, 8 = 가비지.
// 배색은 테트리스 가이드라인의 표준을 따랐다(I 하늘, J 파랑, L 주황, O 노랑,
// S 초록, T 보라, Z 빨강). 가비지만 우리가 정한 회색이다.
//
// 24비트 색으로 적어 두면 되는가? 된다. Bubble Tea 가 터미널의 색 능력을 알아내서
// 필요하면 256색·16색으로 낮춰 준다. 그래서 여기서는 "가장 좋은 색"만 적고,
// 낮추는 일은 라이브러리에 맡긴다.
var CellColors = [9]string{
	"",        // 0 빈칸 — 색 없음
	"#00F0F0", // 1 I
	"#0000F0", // 2 J
	"#F0A000", // 3 L
	"#F0F000", // 4 O
	"#00F000", // 5 S
	"#A000F0", // 6 T
	"#F00000", // 7 Z
	"#787878", // 8 가비지
}

// Cell 은 블록 한 칸. **두 글자**로 그려야 판이 정사각형이 된다.
//
// 터미널의 글자 칸은 세로로 길쭉하다(대략 1:2). 한 칸을 한 글자로 그리면
// 10×20 판이 화면에서는 10×20 이 아니라 홀쭉한 직사각형이 된다.
// 두 글자를 쓰면 가로세로 비율이 맞고, 덤으로 조각이 훨씬 잘 보인다.
const (
	Cell      = "██"
	GhostCell = "░░"
	EmptyCell = "  "
)

// CellStyle 은 칸 값에 맞는 스타일. ghost 면 흐리게 칠한다.
//
// 스타일을 미리 만들어 두지 않고 매번 짓는 이유: 색이 9가지뿐이라 캐시할 만큼
// 비싸지 않고, 캐시하면 초기화 순서에 얽힌 전역 상태가 하나 늘어난다.
func CellStyle(v uint8, ghost bool) lipgloss.Style {
	s := lipgloss.NewStyle()
	if int(v) >= len(CellColors) || CellColors[v] == "" {
		return s
	}
	c := lipgloss.Color(CellColors[v])
	if ghost {
		// 고스트는 배경 없이 글자색만 — 착지 자리를 알려 주되 눈을 뺏지 않는다.
		return s.Foreground(c).Faint(true)
	}
	return s.Foreground(c)
}

// 화면 전반에 쓰는 스타일들.
var (
	TitleStyle  = lipgloss.NewStyle().Bold(true).Foreground(lipgloss.Color("#F0F0F0"))
	LabelStyle  = lipgloss.NewStyle().Foreground(lipgloss.Color("#A0A0A0"))
	ValueStyle  = lipgloss.NewStyle().Bold(true).Foreground(lipgloss.Color("#F0F0F0"))
	DimStyle    = lipgloss.NewStyle().Foreground(lipgloss.Color("#606060"))
	BorderStyle = lipgloss.NewStyle().Foreground(lipgloss.Color("#5050A0"))
	OverStyle   = lipgloss.NewStyle().Bold(true).Foreground(lipgloss.Color("#F00000"))
)
