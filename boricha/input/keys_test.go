package input

import "testing"

// 키 이름은 사용자가 switch 로 비교하는 문자열이다.
// 표기를 Bubble Tea 와 맞춰 두면, 이 덱을 읽고 나서 진짜 Bubble Tea 를 쓸 때
// 손에 익은 그대로 쓸 수 있다. 조합키는 언제나 ctrl → alt → shift 순서다.
func TestKeyString(t *testing.T) {
	cases := []struct {
		key  Key
		want string
	}{
		{Key{Code: 'a', Text: "a"}, "a"},
		{Key{Code: 'A', Text: "A"}, "A"},
		{Key{Code: '한', Text: "한"}, "한"},
		{Key{Code: KeySpace, Text: " "}, "space"},
		{Key{Code: KeyEnter}, "enter"},
		{Key{Code: KeyTab}, "tab"},
		{Key{Code: KeyEscape}, "esc"},
		{Key{Code: KeyBackspace}, "backspace"},
		{Key{Code: KeyUp}, "up"},
		{Key{Code: KeyDown}, "down"},
		{Key{Code: KeyLeft}, "left"},
		{Key{Code: KeyRight}, "right"},
		{Key{Code: KeyHome}, "home"},
		{Key{Code: KeyEnd}, "end"},
		{Key{Code: KeyPgUp}, "pgup"},
		{Key{Code: KeyPgDown}, "pgdown"},
		{Key{Code: KeyInsert}, "insert"},
		{Key{Code: KeyDelete}, "delete"},
		{Key{Code: KeyF1}, "f1"},
		{Key{Code: KeyF12}, "f12"},

		{Key{Code: 'c', Mod: ModCtrl}, "ctrl+c"},
		{Key{Code: 'a', Text: "a", Mod: ModAlt}, "alt+a"},
		{Key{Code: KeyTab, Mod: ModShift}, "shift+tab"},
		{Key{Code: KeyEnter, Mod: ModAlt}, "alt+enter"},
		{Key{Code: KeyLeft, Mod: ModCtrl}, "ctrl+left"},
		{Key{Code: KeyRight, Mod: ModShift | ModCtrl}, "ctrl+shift+right"},
		{Key{Code: 'x', Mod: ModCtrl | ModAlt | ModShift}, "ctrl+alt+shift+x"},
		{Key{Code: KeySpace, Text: " ", Mod: ModCtrl}, "ctrl+space"},
	}
	for _, c := range cases {
		if got := c.key.String(); got != c.want {
			t.Errorf("%+v.String() = %q, 원하는 값 %q", c.key, got, c.want)
		}
	}
}

func TestKeyModContains(t *testing.T) {
	m := ModAlt | ModCtrl
	if !m.Contains(ModCtrl) {
		t.Error("ModAlt|ModCtrl 이 ModCtrl 을 안 담고 있다고 한다")
	}
	if !m.Contains(ModAlt | ModCtrl) {
		t.Error("자기 자신을 안 담고 있다고 한다")
	}
	if m.Contains(ModShift) {
		t.Error("없는 ModShift 를 담고 있다고 한다")
	}
	if (KeyMod(0)).Contains(ModShift) {
		t.Error("빈 묶음이 ModShift 를 담고 있다고 한다")
	}
}

// 특수키 코드는 유니코드 문자와 절대 겹치면 안 된다.
// 겹치는 순간 "위쪽 화살표" 와 어떤 한자가 같은 키가 된다.
func TestSpecialKeysAreBeyondUnicode(t *testing.T) {
	for _, c := range []rune{KeyUp, KeyF12, KeyPgDown} {
		if c <= 0x10FFFF {
			t.Errorf("특수키 코드 %d 가 유니코드 범위 안에 있다", c)
		}
	}
}
