package main

import (
	"strings"
	"testing"

	tea "charm.land/bubbletea/v2"
)

func rune2key(r rune) tea.KeyPressMsg {
	return tea.KeyPressMsg{Code: r, Text: string(r)}
}

func TestRecordsWhatItReceived(t *testing.T) {
	m2, _ := (model{}).Update(rune2key('a'))
	got := m2.(model).View().Content
	for _, want := range []string{"a", "Code", "Text", "Mod"} {
		if !strings.Contains(got, want) {
			t.Errorf("%q 가 화면에 없다:\n%s", want, got)
		}
	}
}

// 특수 키는 Text 가 비어 있다. 그걸 화면에서 눈으로 확인시키는 게 이 예제의 목적이다.
func TestSpecialKeyHasEmptyText(t *testing.T) {
	k := tea.KeyPressMsg{Code: tea.KeyLeft}
	if k.Text != "" {
		t.Fatalf("←의 Text 가 %q 다 — 비어 있어야 한다", k.Text)
	}
	m2, _ := (model{}).Update(k)
	got := m2.(model).View().Content
	if !strings.Contains(got, "left") {
		t.Errorf("키 이름 left 가 없다:\n%s", got)
	}
	if !strings.Contains(got, "(없음)") {
		t.Errorf("빈 Text 표시가 없다:\n%s", got)
	}
}

func TestModifierIsShown(t *testing.T) {
	m2, _ := (model{}).Update(tea.KeyPressMsg{Code: 'a', Mod: tea.ModAlt})
	got := m2.(model).View().Content
	if !strings.Contains(got, "alt+a") {
		t.Errorf("alt+a 가 없다:\n%s", got)
	}
}

// 기록은 최근 것부터, 최대 histMax 줄까지만 남는다.
// 상한이 없으면 화면이 넘쳐 스크롤이 필요해진다.
func TestHistoryIsCapped(t *testing.T) {
	var m tea.Model = model{}
	for i := 0; i < histMax+5; i++ {
		m, _ = m.Update(rune2key(rune('a' + i%26)))
	}
	if n := len(m.(model).hist); n != histMax {
		t.Errorf("기록이 %d줄이다 — %d줄로 잘려야 한다", n, histMax)
	}
}

func TestNewestFirst(t *testing.T) {
	var m tea.Model = model{}
	m, _ = m.Update(rune2key('x'))
	m, _ = m.Update(rune2key('y'))
	h := m.(model).hist
	if len(h) < 2 {
		t.Fatalf("기록이 %d줄뿐이다", len(h))
	}
	if !strings.Contains(h[0], "y") {
		t.Errorf("맨 위가 최신이 아니다: %q", h[0])
	}
}

// ctrl+c 만 프로그램을 끝낸다 — q 는 "그냥 q 키"로 보여야 하니까.
func TestOnlyCtrlCQuits(t *testing.T) {
	if _, cmd := (model{}).Update(rune2key('q')); cmd != nil {
		t.Error("q 가 프로그램을 끝냈다 — 이 예제에서는 q 도 그냥 키다")
	}
	_, cmd := (model{}).Update(tea.KeyPressMsg{Code: 'c', Mod: tea.ModCtrl})
	if cmd == nil {
		t.Fatal("ctrl+c 가 무시됐다")
	}
	if _, ok := cmd().(tea.QuitMsg); !ok {
		t.Errorf("Quit 이 아니라 %T", cmd())
	}
}

func TestEmptyStateHasHint(t *testing.T) {
	if !strings.Contains((model{}).View().Content, "아무 키나") {
		t.Error("첫 화면에 안내가 없다")
	}
}
