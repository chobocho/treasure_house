package main

import (
	"strings"
	"testing"

	tea "charm.land/bubbletea/v2"

	"charm.land/lipgloss/v2"
)

func rune2key(r rune) tea.KeyPressMsg {
	return tea.KeyPressMsg{Code: r, Text: string(r)}
}

// 스타일은 값이다. 메서드는 새 Style 을 돌려주고 원본은 그대로다 —
// Bubble Tea 모델과 똑같은 규칙이라 한 번에 익혀 둔다.
func TestStyleIsAValue(t *testing.T) {
	base := lipgloss.NewStyle().Bold(true)
	derived := base.Italic(true)
	if base.GetItalic() {
		t.Error("원본 스타일이 바뀌었다")
	}
	if !derived.GetItalic() || !derived.GetBold() {
		t.Error("파생 스타일이 둘 다 갖고 있지 않다")
	}
}

// 폭을 고정하면 짧은 줄은 채워지고 긴 줄은 접힌다.
// 보드 옆 패널의 폭을 맞출 때 쓰는 성질이라 여기서 못 박아 둔다.
func TestFixedWidthPadsAndWraps(t *testing.T) {
	s := lipgloss.NewStyle().Width(10)
	if w := lipgloss.Width(s.Render("짧음")); w != 10 {
		t.Errorf("짧은 줄의 폭이 %d 다", w)
	}
	tall := s.Render("이 문장은 열 칸보다 훨씬 길어서 반드시 접힌다")
	if lipgloss.Height(tall) < 2 {
		t.Error("긴 문장이 접히지 않았다")
	}
	if w := lipgloss.Width(tall); w > 10 {
		t.Errorf("접혔는데도 폭이 %d 다", w)
	}
}

// 한글은 한 글자가 두 칸이다. len() 으로 폭을 재면 판이 어긋난다 —
// 이 덱이 블록을 두 글자(██)로 그리는 이유이기도 하다.
func TestWideRunesCountAsTwoCells(t *testing.T) {
	if w := lipgloss.Width("한글"); w != 4 {
		t.Errorf("\"한글\"의 폭이 %d 다 — 4 여야 한다", w)
	}
	if n := len("한글"); n == 4 {
		t.Error("len() 이 우연히 맞았다 — 테스트의 전제가 무너졌다")
	}
	if w := lipgloss.Width(cell); w != 2 {
		t.Errorf("블록 한 칸(%q)의 폭이 %d 다 — 2 여야 한다", cell, w)
	}
}

// JoinHorizontal 은 높이가 다른 두 덩어리를 나란히 붙인다.
// 결과 높이는 더 높은 쪽, 폭은 둘의 합이다.
func TestJoinHorizontal(t *testing.T) {
	left := "1\n2\n3"
	right := "a"
	got := lipgloss.JoinHorizontal(lipgloss.Top, left, right)
	if h := lipgloss.Height(got); h != 3 {
		t.Errorf("높이가 %d 다", h)
	}
	if w := lipgloss.Width(got); w != 2 {
		t.Errorf("폭이 %d 다", w)
	}
}

func TestViewHasAllThreePanels(t *testing.T) {
	m2, _ := (model{}).Update(tea.WindowSizeMsg{Width: 80, Height: 24})
	got := m2.(model).View().Content
	for _, want := range []string{"제목", "왼쪽", "오른쪽"} {
		if !strings.Contains(got, want) {
			t.Errorf("%q 패널이 없다:\n%s", want, got)
		}
	}
}

// 테두리를 켜고 끄는 키. 테두리는 폭을 2 늘린다 — 레이아웃 계산에서 잊기 쉬운 부분이다.
func TestBorderToggleChangesWidth(t *testing.T) {
	m2, _ := (model{}).Update(tea.WindowSizeMsg{Width: 80, Height: 24})
	on := m2.(model).View().Content
	m3, _ := m2.Update(rune2key('b'))
	if m3.(model).border {
		t.Error("b 로 테두리가 꺼지지 않았다")
	}
	off := m3.(model).View().Content
	if lipgloss.Width(on) <= lipgloss.Width(off) {
		t.Errorf("테두리 있는 쪽(%d)이 없는 쪽(%d)보다 넓지 않다",
			lipgloss.Width(on), lipgloss.Width(off))
	}
}

func TestQuitKey(t *testing.T) {
	_, cmd := (model{}).Update(rune2key('q'))
	if cmd == nil {
		t.Fatal("q 가 무시됐다")
	}
	if _, ok := cmd().(tea.QuitMsg); !ok {
		t.Errorf("Quit 이 아니라 %T", cmd())
	}
}
