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

// 크기를 아직 모르는 상태(첫 WindowSizeMsg 이전)에도 화면이 나와야 한다.
// 이때 0×0 으로 계산하다 음수 폭이 나오면 lipgloss 가 패닉한다 — 실제로 밟는 함정이다.
func TestZeroSizeDoesNotPanic(t *testing.T) {
	got := (model{}).View().Content
	if got == "" {
		t.Error("크기를 모를 때 화면이 비어 있다")
	}
}

func TestWindowSizeIsStored(t *testing.T) {
	m2, _ := (model{}).Update(tea.WindowSizeMsg{Width: 100, Height: 40})
	m := m2.(model)
	if m.w != 100 || m.h != 40 {
		t.Errorf("크기가 %d×%d 로 들어갔다", m.w, m.h)
	}
}

// 최소 크기 미만이면 상자 대신 안내를 띄운다. 지금 크기와 필요한 크기를 둘 다 말해 준다.
func TestTooSmallShowsWhatIsNeeded(t *testing.T) {
	m2, _ := (model{}).Update(tea.WindowSizeMsg{Width: 30, Height: 8})
	got := m2.(model).View().Content
	if !strings.Contains(got, "30") || !strings.Contains(got, "8") {
		t.Errorf("지금 크기가 안내에 없다:\n%s", got)
	}
	if !strings.Contains(got, "40") || !strings.Contains(got, "12") {
		t.Errorf("필요한 크기(%d×%d)가 안내에 없다:\n%s", minW, minH, got)
	}
}

// 충분히 크면 상자가 화면 한가운데 놓인다. Place 가 만든 결과의 크기가
// 창 크기와 정확히 같아야 한다 — 한 줄이라도 넘치면 터미널이 스크롤된다.
func TestBoxFillsExactlyTheWindow(t *testing.T) {
	for _, sz := range []tea.WindowSizeMsg{{Width: 80, Height: 24}, {Width: 40, Height: 12}, {Width: 200, Height: 60}} {
		m2, _ := (model{}).Update(sz)
		got := m2.(model).View().Content
		w, h := lipgloss.Size(got)
		if w > sz.Width || h > sz.Height {
			t.Errorf("%d×%d 창에 %d×%d 짜리 화면을 그렸다", sz.Width, sz.Height, w, h)
		}
		if h != sz.Height {
			t.Errorf("%d×%d 창인데 높이가 %d 다 — 세로 가운데 정렬이 안 됐다", sz.Width, sz.Height, h)
		}
	}
}

func TestBoxShowsSize(t *testing.T) {
	m2, _ := (model{}).Update(tea.WindowSizeMsg{Width: 80, Height: 24})
	got := m2.(model).View().Content
	if !strings.Contains(got, "80") || !strings.Contains(got, "24") {
		t.Errorf("상자에 창 크기가 안 적혀 있다:\n%s", got)
	}
}

// 경계값: 딱 최소 크기면 상자가 나와야 하고, 1 작으면 안내가 나와야 한다.
func TestMinimumSizeBoundary(t *testing.T) {
	m2, _ := (model{}).Update(tea.WindowSizeMsg{Width: minW, Height: minH})
	if strings.Contains(m2.(model).View().Content, "키워") {
		t.Error("딱 최소 크기인데 안내가 떴다")
	}
	m3, _ := (model{}).Update(tea.WindowSizeMsg{Width: minW - 1, Height: minH})
	if !strings.Contains(m3.(model).View().Content, "키워") {
		t.Error("최소보다 1 좁은데 안내가 안 떴다")
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
