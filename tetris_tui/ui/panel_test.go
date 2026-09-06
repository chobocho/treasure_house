package ui

import (
	"strings"
	"testing"

	"charm.land/lipgloss/v2"

	"treasure/tetris_tui/core"
)

func sampleStats() core.Stats {
	return core.Stats{Score: 12345, Level: 3, Lines: 27, Hold: core.PieceT, Combo: 2}
}

// 패널의 폭은 고정이다. 점수가 몇 자리든 옆의 판이 밀리면 안 된다.
func TestPanelWidthIsFixed(t *testing.T) {
	for _, score := range []int32{0, 999, 1234567} {
		s := sampleStats()
		s.Score = score
		got := RenderPanel(s, []int{0, 1, 2}, "도움말")
		if w := lipgloss.Width(got); w != PanelWidth {
			t.Errorf("점수 %d 일 때 패널 폭이 %d — %d 여야 한다", score, w, PanelWidth)
		}
	}
}

func TestPanelShowsTheNumbers(t *testing.T) {
	got := RenderPanel(sampleStats(), []int{0, 1, 2}, "")
	for _, want := range []string{"12345", "3", "27"} {
		if !strings.Contains(got, want) {
			t.Errorf("패널에 %q 가 없다:\n%s", want, got)
		}
	}
}

// 홀드가 비어 있어도(-1) 자리는 그대로 남아야 한다.
func TestPanelWithEmptyHold(t *testing.T) {
	s := sampleStats()
	s.Hold = -1
	withHold := RenderPanel(sampleStats(), []int{0}, "")
	without := RenderPanel(s, []int{0}, "")
	if lipgloss.Height(withHold) != lipgloss.Height(without) {
		t.Errorf("홀드 유무로 패널 높이가 %d → %d 로 바뀌었다",
			lipgloss.Height(withHold), lipgloss.Height(without))
	}
}

// 다음 조각을 몇 개 보여 주든 죽지 않아야 한다.
func TestPanelWithVaryingNextCount(t *testing.T) {
	for _, n := range [][]int{nil, {0}, {0, 1, 2, 3, 4}} {
		got := RenderPanel(sampleStats(), n, "")
		if lipgloss.Width(got) != PanelWidth {
			t.Errorf("다음 조각 %d개일 때 폭이 %d 다", len(n), lipgloss.Width(got))
		}
	}
}

// 범위 밖 조각 번호가 와도 죽지 않아야 한다.
func TestPanelSurvivesBadPieceNumbers(t *testing.T) {
	s := sampleStats()
	s.Hold = 99
	got := RenderPanel(s, []int{-5, 42}, "")
	if lipgloss.Width(got) != PanelWidth {
		t.Errorf("이상한 조각 번호에 폭이 %d 로 깨졌다", lipgloss.Width(got))
	}
}
