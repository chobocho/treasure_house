package widgets

import (
	"strings"
	"testing"

	"treasure/boricha/tea"
	"treasure/boricha/width"
)

func items(names ...string) []Item {
	out := make([]Item, len(names))
	for i, n := range names {
		out[i] = StringItem(n)
	}
	return out
}

var teas = items("보리차", "녹차", "홍차", "우롱차", "메밀차", "둥굴레차", "black tea", "green tea")

func key(s string) tea.KeyMsg {
	switch s {
	case "up":
		return tea.KeyMsg{Code: tea.KeyUp}
	case "down":
		return tea.KeyMsg{Code: tea.KeyDown}
	case "home":
		return tea.KeyMsg{Code: tea.KeyHome}
	case "end":
		return tea.KeyMsg{Code: tea.KeyEnd}
	case "enter":
		return tea.KeyMsg{Code: tea.KeyEnter}
	case "esc":
		return tea.KeyMsg{Code: tea.KeyEscape}
	}
	r := []rune(s)[0]
	return tea.KeyMsg{Code: r, Text: s}
}

func sendAll(l List, keys ...string) List {
	for _, k := range keys {
		l, _ = l.Update(key(k))
	}
	return l
}

// 화면은 언제나 정확히 Height 줄, Width 칸이다.
func TestListShapeIsFixed(t *testing.T) {
	for _, h := range []int{3, 6, 12} {
		for _, n := range []int{0, 1, 8} {
			l := NewList(teas[:n], 24, h)
			l.Title = "차 고르기"
			got := strings.Split(l.View(), "\n")
			if len(got) != h {
				t.Errorf("항목 %d개·높이 %d 인데 화면이 %d줄", n, h, len(got))
				continue
			}
			for i, line := range got {
				if w := width.StringWidth(line); w != 24 {
					t.Errorf("항목 %d개·높이 %d, 줄 %d 이 %d칸: %q", n, h, i, w, line)
				}
			}
		}
	}
}

func TestListCursor(t *testing.T) {
	l := NewList(teas, 24, 12)
	if l.Index() != 0 || l.SelectedItem().Title() != "보리차" {
		t.Fatalf("처음 = %d %v", l.Index(), l.SelectedItem())
	}
	l = sendAll(l, "down", "down")
	if l.Index() != 2 || l.SelectedItem().Title() != "홍차" {
		t.Errorf("두 칸 내린 뒤 = %d %q", l.Index(), l.SelectedItem().Title())
	}
	l = sendAll(l, "j")
	if l.Index() != 3 {
		t.Errorf("j 뒤 = %d", l.Index())
	}
	// 끝을 넘지 않는다
	l = sendAll(l, "end")
	if l.Index() != len(teas)-1 {
		t.Errorf("end 뒤 = %d", l.Index())
	}
	l = sendAll(l, "down", "down")
	if l.Index() != len(teas)-1 {
		t.Errorf("끝을 넘어갔다: %d", l.Index())
	}
	l = sendAll(l, "home", "up")
	if l.Index() != 0 {
		t.Errorf("처음보다 앞으로 갔다: %d", l.Index())
	}
}

// 항목이 없으면 고른 것도 없다. nil 을 돌려주는 것이 정직하다.
func TestListEmpty(t *testing.T) {
	l := NewList(nil, 20, 5)
	if l.SelectedItem() != nil {
		t.Error("빈 목록인데 고른 항목이 있다")
	}
	l = sendAll(l, "down", "up", "enter")
	if l.Index() != 0 {
		t.Errorf("빈 목록에서 커서가 %d", l.Index())
	}
}

// 화면보다 항목이 많으면 커서를 따라 목록이 굴러간다. 커서는 언제나 보인다.
func TestListScrollsToKeepCursorVisible(t *testing.T) {
	l := NewList(teas, 24, 5) // 제목 없음, 상태줄 1 → 항목은 4줄
	l = sendAll(l, "end")
	v := l.View()
	if !strings.Contains(v, "green tea") {
		t.Errorf("맨 아래인데 마지막 항목이 안 보인다:\n%s", v)
	}
	if strings.Contains(v, "보리차") {
		t.Errorf("맨 아래인데 첫 항목이 아직 보인다:\n%s", v)
	}
	l = sendAll(l, "home")
	if !strings.Contains(l.View(), "보리차") {
		t.Errorf("맨 위인데 첫 항목이 안 보인다:\n%s", l.View())
	}
}

// 고른 항목에는 표시가 붙는다.
func TestListCursorMark(t *testing.T) {
	l := NewList(teas, 24, 12)
	l.Cursor = "▸ "
	if !strings.Contains(l.View(), "▸ 보리차") {
		t.Errorf("표시가 없다:\n%s", l.View())
	}
	l = sendAll(l, "down")
	v := l.View()
	if !strings.Contains(v, "▸ 녹차") || strings.Contains(v, "▸ 보리차") {
		t.Errorf("표시가 안 따라왔다:\n%s", v)
	}
}

// / 로 거르기에 들어가고, 글자를 치면 목록이 좁아진다.
func TestListFilter(t *testing.T) {
	l := NewList(teas, 30, 12)
	l = sendAll(l, "/")
	if !l.Filtering() {
		t.Fatal("/ 를 눌러도 거르기로 안 들어갔다")
	}
	l = sendAll(l, "차")
	if l.FilterValue() != "차" {
		t.Errorf("거르는 말 = %q", l.FilterValue())
	}
	got := l.VisibleItems()
	if len(got) != 6 {
		t.Errorf("'차' 로 걸러 %d개, 원하는 값 6개: %v", len(got), titles(got))
	}
	// 확정하면 거르기는 남고 입력만 끝난다
	l = sendAll(l, "enter")
	if l.Filtering() {
		t.Error("enter 뒤에도 입력 중이라고 한다")
	}
	if len(l.VisibleItems()) != 6 {
		t.Error("enter 뒤에 거르기가 풀렸다")
	}
	// esc 로 되돌린다
	l = sendAll(l, "esc")
	if len(l.VisibleItems()) != len(teas) {
		t.Errorf("esc 뒤 = %d개", len(l.VisibleItems()))
	}
}

// 거르기는 대소문자를 가리지 않는다.
func TestListFilterIgnoresCase(t *testing.T) {
	l := NewList(teas, 30, 12)
	l = sendAll(l, "/", "T", "E", "A")
	if n := len(l.VisibleItems()); n != 2 {
		t.Errorf("'TEA' 로 걸러 %d개, 원하는 값 2개: %v", n, titles(l.VisibleItems()))
	}
}

// 걸러진 뒤에도 커서는 보이는 항목 안에 있어야 한다.
func TestListFilterClampsCursor(t *testing.T) {
	l := NewList(teas, 30, 12)
	l = sendAll(l, "end") // 마지막으로
	l = sendAll(l, "/", "녹")
	if l.Index() != 0 {
		t.Errorf("걸러진 뒤 커서 = %d, 원하는 값 0", l.Index())
	}
	if l.SelectedItem().Title() != "녹차" {
		t.Errorf("고른 항목 = %q", l.SelectedItem().Title())
	}
}

// 거르는 동안에는 j·k 가 글자로 들어가야 한다. 안 그러면 "japan" 을 칠 수 없다.
func TestListFilterTypingIsNotNavigation(t *testing.T) {
	l := NewList(items("java", "kotlin", "go"), 30, 12)
	l = sendAll(l, "/", "j")
	if l.FilterValue() != "j" {
		t.Errorf("거르는 말 = %q — j 가 이동으로 먹혔다", l.FilterValue())
	}
}

func TestListSetItems(t *testing.T) {
	l := NewList(teas, 24, 12)
	l = sendAll(l, "end")
	l = l.SetItems(teas[:2])
	if l.Index() > 1 {
		t.Errorf("항목이 줄었는데 커서가 %d", l.Index())
	}
}

func TestListKeyBindings(t *testing.T) {
	if len(NewList(teas, 24, 12).KeyBindings()) < 3 {
		t.Error("배치가 너무 적다")
	}
}

func titles(its []Item) []string {
	out := make([]string, len(its))
	for i, it := range its {
		out[i] = it.Title()
	}
	return out
}
