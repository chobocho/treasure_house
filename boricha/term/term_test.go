package term

import (
	"bytes"
	"strings"
	"testing"
)

func newTestTerm() (*Term, *bytes.Buffer) {
	var buf bytes.Buffer
	return New(strings.NewReader(""), &buf), &buf
}

// 터미널을 켜고 끄는 일은 전부 "정해진 바이트를 내보내는 것"이다.
// 그래서 진짜 터미널 없이도 출력을 버퍼로 받아 그대로 검사할 수 있다.
func TestTermWritesSequences(t *testing.T) {
	cases := []struct {
		name string
		call func(*Term) error
		want string
	}{
		{"EnterAltScreen", (*Term).EnterAltScreen, EnterAltScreen},
		{"ExitAltScreen", (*Term).ExitAltScreen, ExitAltScreen},
		{"HideCursor", (*Term).HideCursor, HideCursor},
		{"ShowCursor", (*Term).ShowCursor, ShowCursor},
		{"EnablePaste", (*Term).EnablePaste, EnablePaste},
		{"DisablePaste", (*Term).DisablePaste, DisablePaste},
		{"EnableFocus", (*Term).EnableFocus, EnableFocus},
		{"DisableFocus", (*Term).DisableFocus, DisableFocus},
	}
	for _, c := range cases {
		tm, buf := newTestTerm()
		if err := c.call(tm); err != nil {
			t.Fatalf("%s: %v", c.name, err)
		}
		if got := buf.String(); got != c.want {
			t.Errorf("%s 가 %q 를 썼다, 원하는 값 %q", c.name, got, c.want)
		}
	}
}

func TestEnableMouse(t *testing.T) {
	tm, buf := newTestTerm()
	if err := tm.EnableMouse(false); err != nil {
		t.Fatal(err)
	}
	if got := buf.String(); got != EnableMouse {
		t.Errorf("EnableMouse(false) = %q, 원하는 값 %q", got, EnableMouse)
	}
	tm, buf = newTestTerm()
	if err := tm.EnableMouse(true); err != nil {
		t.Fatal(err)
	}
	if got := buf.String(); got != EnableMouseAll {
		t.Errorf("EnableMouse(true) = %q, 원하는 값 %q", got, EnableMouseAll)
	}
}

// 마우스는 켤 때 쓴 모드로 꺼야 한다. 1003 으로 켜 놓고 1002 로 끄면
// 터미널에 추적이 켜진 채로 남아, 프로그램이 끝난 뒤 셸에서 마우스를 움직일 때마다
// 쓰레기 바이트가 쏟아진다.
func TestDisableMouseMatchesEnable(t *testing.T) {
	tm, buf := newTestTerm()
	_ = tm.EnableMouse(true)
	buf.Reset()
	_ = tm.DisableMouse()
	if got := buf.String(); got != DisableMouseAll {
		t.Errorf("all 모드로 켠 뒤 끄기 = %q, 원하는 값 %q", got, DisableMouseAll)
	}
}

// 정리는 켠 순서의 역순이어야 한다. 대체 화면을 먼저 빠져나가 버리면
// 그 뒤에 내보내는 "커서 보이기" 가 원래 화면에 적용되어, 대체 화면 쪽 커서는 숨은 채 남는다.
func TestCleanupUndoesInReverseOrder(t *testing.T) {
	tm, buf := newTestTerm()
	_ = tm.EnterAltScreen()
	_ = tm.HideCursor()
	_ = tm.EnableMouse(false)
	_ = tm.EnablePaste()
	buf.Reset()

	if err := tm.Cleanup(); err != nil {
		t.Fatal(err)
	}
	want := DisablePaste + DisableMouse + ShowCursor + ExitAltScreen
	if got := buf.String(); got != want {
		t.Errorf("Cleanup = %q\n원하는 값        %q", got, want)
	}
}

// 켜지 않은 것을 끄지 않는다. 두 번 불러도 같아야 한다(멱등).
func TestCleanupOnlyUndoesWhatWasSet(t *testing.T) {
	tm, buf := newTestTerm()
	_ = tm.HideCursor()
	buf.Reset()
	_ = tm.Cleanup()
	if got := buf.String(); got != ShowCursor {
		t.Errorf("Cleanup = %q, 원하는 값 %q", got, ShowCursor)
	}
	buf.Reset()
	_ = tm.Cleanup()
	if got := buf.String(); got != "" {
		t.Errorf("두 번째 Cleanup 이 %q 를 더 썼다", got)
	}
}

// Restore 는 defer 로 걸어 두는 함수다. 원시 모드로 들어간 적이 없어도
// 조용히 아무 일도 하지 않아야, 어느 경로로 빠져나가든 defer 를 그대로 둘 수 있다.
func TestRestoreWithoutMakeRawIsNoop(t *testing.T) {
	tm, _ := newTestTerm()
	if err := tm.Restore(); err != nil {
		t.Errorf("Restore() = %v, 원하는 값 nil", err)
	}
}

// 파일이 아닌 것(버퍼)에는 원시 모드도 크기도 없다. 프로그램이 이 오류를 보고
// 80×24 로 물러설 수 있도록, 거짓말 대신 오류를 준다.
func TestNonTTY(t *testing.T) {
	tm, _ := newTestTerm()
	if tm.IsTTY() {
		t.Error("bytes.Buffer 를 터미널이라고 한다")
	}
	if _, _, err := tm.Size(); err == nil {
		t.Error("Size() 가 터미널이 아닌 곳에서 오류를 안 냈다")
	}
	if err := tm.MakeRaw(); err == nil {
		t.Error("MakeRaw() 가 터미널이 아닌 곳에서 오류를 안 냈다")
	}
}
