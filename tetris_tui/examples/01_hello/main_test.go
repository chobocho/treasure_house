package main

import (
	"strings"
	"testing"

	tea "charm.land/bubbletea/v2"
)

// Bubble Tea 모델은 그냥 값이다. 프로그램을 띄우지 않고, 터미널도 없이,
// Update 에 메시지를 직접 넣어서 테스트할 수 있다.
// 이 덱의 모든 모델 테스트가 이 모양이다 — teatest 같은 별도 도구가 필요 없다.
func rune2key(r rune) tea.KeyPressMsg {
	return tea.KeyPressMsg{Code: r, Text: string(r)}
}

func TestInitDoesNothing(t *testing.T) {
	if cmd := (model{}).Init(); cmd != nil {
		t.Fatalf("Init 이 nil 이 아닌 Cmd 를 돌려줬다: %v", cmd)
	}
}

func TestViewShowsWelcome(t *testing.T) {
	got := (model{}).View().Content
	if !strings.Contains(got, "Bubble Tea") {
		t.Errorf("환영 문구가 없다:\n%s", got)
	}
	if !strings.Contains(got, "q") {
		t.Errorf("종료 안내가 없다:\n%s", got)
	}
}

func TestQuitKeys(t *testing.T) {
	keys := []tea.KeyPressMsg{
		rune2key('q'),
		{Code: tea.KeyEscape},
		{Code: 'c', Mod: tea.ModCtrl},
	}
	for _, k := range keys {
		m2, cmd := (model{}).Update(k)
		if cmd == nil {
			t.Fatalf("%q: Cmd 가 nil 이다", k.String())
		}
		if _, ok := cmd().(tea.QuitMsg); !ok {
			t.Errorf("%q: Quit 이 아니라 %T 를 돌려줬다", k.String(), cmd())
		}
		if !m2.(model).quitting {
			t.Errorf("%q: quitting 이 켜지지 않았다", k.String())
		}
	}
}

// 키 이름 문자열은 우리가 지어낸 게 아니라 라이브러리가 만든다.
// 이름이 바뀌면 위 switch 가 조용히 죽으므로, 가정을 테스트로 못 박아 둔다.
func TestKeyNamesAreWhatWeAssume(t *testing.T) {
	cases := []struct {
		key  tea.KeyPressMsg
		want string
	}{
		{rune2key('q'), "q"},
		{tea.KeyPressMsg{Code: tea.KeyEscape}, "esc"},
		{tea.KeyPressMsg{Code: 'c', Mod: tea.ModCtrl}, "ctrl+c"},
		{tea.KeyPressMsg{Code: tea.KeyLeft}, "left"},
		{tea.KeyPressMsg{Code: tea.KeySpace}, "space"},
	}
	for _, c := range cases {
		if got := c.key.String(); got != c.want {
			t.Errorf("키 이름이 %q 다 — %q 를 기대했다", got, c.want)
		}
	}
}

// 다른 키는 아무 일도 일으키지 않아야 한다. 모델도 그대로여야 한다(값 복사 확인).
func TestUnknownKeyIgnored(t *testing.T) {
	m2, cmd := (model{}).Update(rune2key('z'))
	if cmd != nil {
		t.Errorf("Cmd 가 nil 이 아니다: %v", cmd())
	}
	if m2.(model).quitting {
		t.Error("엉뚱한 키에 quitting 이 켜졌다")
	}
}

// 창 크기 메시지처럼 모르는 메시지가 와도 죽지 않아야 한다.
func TestUnknownMsgIsSafe(t *testing.T) {
	if _, cmd := (model{}).Update(tea.WindowSizeMsg{Width: 80, Height: 24}); cmd != nil {
		t.Errorf("Cmd 가 nil 이 아니다: %v", cmd())
	}
}

func TestFarewellView(t *testing.T) {
	got := model{quitting: true}.View().Content
	if !strings.Contains(got, "안녕히") {
		t.Errorf("작별 인사가 없다:\n%s", got)
	}
}
