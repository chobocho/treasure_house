package term

import "testing"

// 시퀀스는 "바이트가 정확히 이것"이 전부인 코드다. 그래서 테스트도 바이트 비교다.
// 한 글자만 틀려도 터미널은 그것을 명령이 아니라 글자로 찍어 버린다 —
// 화면에 `[?1049h` 같은 쓰레기가 남는 실패는 전부 이 표의 오타에서 온다.
func TestSequenceBytes(t *testing.T) {
	cases := []struct{ name, got, want string }{
		{"ESC", ESC, "\x1b"},
		{"CSI", CSI, "\x1b["},
		{"Reset", Reset, "\x1b[0m"},
		{"ClearScreen", ClearScreen, "\x1b[2J"},
		{"ClearLine", ClearLine, "\x1b[2K"},
		{"ClearToEOL", ClearToEOL, "\x1b[K"},
		{"CursorHome", CursorHome, "\x1b[H"},
		{"HideCursor", HideCursor, "\x1b[?25l"},
		{"ShowCursor", ShowCursor, "\x1b[?25h"},
		{"EnterAltScreen", EnterAltScreen, "\x1b[?1049h"},
		{"ExitAltScreen", ExitAltScreen, "\x1b[?1049l"},
		{"EnableMouse", EnableMouse, "\x1b[?1002h\x1b[?1006h"},
		{"DisableMouse", DisableMouse, "\x1b[?1006l\x1b[?1002l"},
		{"EnableMouseAll", EnableMouseAll, "\x1b[?1003h\x1b[?1006h"},
		{"DisableMouseAll", DisableMouseAll, "\x1b[?1006l\x1b[?1003l"},
		{"EnablePaste", EnablePaste, "\x1b[?2004h"},
		{"DisablePaste", DisablePaste, "\x1b[?2004l"},
		{"EnableFocus", EnableFocus, "\x1b[?1004h"},
		{"DisableFocus", DisableFocus, "\x1b[?1004l"},
		{"BeginSync", BeginSync, "\x1b[?2026h"},
		{"EndSync", EndSync, "\x1b[?2026l"},
	}
	for _, c := range cases {
		if c.got != c.want {
			t.Errorf("%s = %q, 원하는 값 %q", c.name, c.got, c.want)
		}
	}
}

// 커서 이동은 매개변수가 붙는 시퀀스다. 1부터 세는 좌표계라는 점,
// 그리고 "생략하면 1"이라는 규칙(ECMA-48 기본값)을 지켜야 한다.
func TestCursorTo(t *testing.T) {
	cases := []struct {
		row, col int
		want     string
	}{
		{1, 1, "\x1b[1;1H"},
		{24, 80, "\x1b[24;80H"},
		{0, 0, "\x1b[1;1H"},   // 0 이나 음수는 1 로 올려 준다
		{-3, -1, "\x1b[1;1H"}, // 호출하는 쪽이 0 부터 세다 실수해도 화면이 깨지지 않게
		{10, 200, "\x1b[10;200H"},
	}
	for _, c := range cases {
		if got := CursorTo(c.row, c.col); got != c.want {
			t.Errorf("CursorTo(%d,%d) = %q, 원하는 값 %q", c.row, c.col, got, c.want)
		}
	}
}

func TestCursorMoves(t *testing.T) {
	cases := []struct{ name, got, want string }{
		{"Up(1)", CursorUp(1), "\x1b[1A"},
		{"Up(0)", CursorUp(0), ""},   // 0칸 이동은 시퀀스를 아예 내보내지 않는다
		{"Up(-2)", CursorUp(-2), ""}, // 음수도 마찬가지 — 빈 문자열이 곧 "아무 일 없음"
		{"Down(3)", CursorDown(3), "\x1b[3B"},
		{"Down(0)", CursorDown(0), ""},
		{"ToCol(1)", CursorToCol(1), "\x1b[1G"},
		{"ToCol(0)", CursorToCol(0), "\x1b[1G"},
		{"ToCol(80)", CursorToCol(80), "\x1b[80G"},
	}
	for _, c := range cases {
		if c.got != c.want {
			t.Errorf("%s = %q, 원하는 값 %q", c.name, c.got, c.want)
		}
	}
}
