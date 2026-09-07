package widgets

import (
	"strings"
	"testing"

	"treasure/boricha/tea"
	"treasure/boricha/width"
)

func typeKeys(ti TextInput, s string) TextInput {
	for _, r := range s {
		ti, _ = ti.Update(tea.KeyMsg{Code: r, Text: string(r)})
	}
	return ti
}

func press(ti TextInput, names ...string) TextInput {
	codes := map[string]rune{
		"left": tea.KeyLeft, "right": tea.KeyRight, "home": tea.KeyHome, "end": tea.KeyEnd,
		"backspace": tea.KeyBackspace, "delete": tea.KeyDelete,
	}
	for _, n := range names {
		if c, ok := codes[n]; ok {
			ti, _ = ti.Update(tea.KeyMsg{Code: c})
			continue
		}
		// ctrl+x 꼴
		ti, _ = ti.Update(tea.KeyMsg{Code: rune(n[len(n)-1]), Mod: tea.ModCtrl})
	}
	return ti
}

func TestTextInputTyping(t *testing.T) {
	ti := NewTextInput().Focus()
	ti = typeKeys(ti, "hello")
	if ti.Value() != "hello" {
		t.Errorf("= %q", ti.Value())
	}
	if ti.Position() != 5 {
		t.Errorf("커서 = %d, 원하는 값 5", ti.Position())
	}
}

// 한글은 룬 하나가 세 바이트다. 바이트로 세면 백스페이스 한 번에 글자가 깨진다.
func TestTextInputKorean(t *testing.T) {
	ti := typeKeys(NewTextInput().Focus(), "보리차")
	if ti.Value() != "보리차" {
		t.Errorf("= %q", ti.Value())
	}
	if ti.Position() != 3 {
		t.Errorf("커서 = %d, 원하는 값 3 (룬 단위)", ti.Position())
	}
	ti = press(ti, "backspace")
	if ti.Value() != "보리" {
		t.Errorf("백스페이스 뒤 = %q, 원하는 값 %q", ti.Value(), "보리")
	}
}

func TestTextInputCursorMoves(t *testing.T) {
	ti := typeKeys(NewTextInput().Focus(), "한a글")
	ti = press(ti, "left", "left")
	if ti.Position() != 1 {
		t.Fatalf("커서 = %d, 원하는 값 1", ti.Position())
	}
	ti = typeKeys(ti, "X")
	if ti.Value() != "한Xa글" {
		t.Errorf("가운데 삽입 = %q", ti.Value())
	}
	ti = press(ti, "home")
	if ti.Position() != 0 {
		t.Errorf("home 뒤 커서 = %d", ti.Position())
	}
	ti = press(ti, "end")
	if ti.Position() != 4 {
		t.Errorf("end 뒤 커서 = %d", ti.Position())
	}
	// 끝에서 더 가도 넘어가지 않는다
	ti = press(ti, "right", "right")
	if ti.Position() != 4 {
		t.Errorf("끝을 넘어갔다: %d", ti.Position())
	}
	ti = press(ti, "home", "left")
	if ti.Position() != 0 {
		t.Errorf("처음보다 앞으로 갔다: %d", ti.Position())
	}
}

func TestTextInputDelete(t *testing.T) {
	ti := typeKeys(NewTextInput().Focus(), "abc")
	ti = press(ti, "home", "delete")
	if ti.Value() != "bc" {
		t.Errorf("delete 뒤 = %q", ti.Value())
	}
	// 빈 상태에서 지워도 죽지 않는다
	ti = press(ti, "delete", "delete", "delete", "backspace")
	if ti.Value() != "" {
		t.Errorf("= %q", ti.Value())
	}
}

// ctrl+u 는 전부 지우기, ctrl+w 는 낱말 하나 지우기 — 셸에서 온 관습이다.
func TestTextInputWordAndLineDelete(t *testing.T) {
	ti := typeKeys(NewTextInput().Focus(), "보리차 한 잔")
	ti = press(ti, "w")
	if ti.Value() != "보리차 한 " {
		t.Errorf("ctrl+w 뒤 = %q, 원하는 값 %q", ti.Value(), "보리차 한 ")
	}
	ti = press(ti, "u")
	if ti.Value() != "" {
		t.Errorf("ctrl+u 뒤 = %q", ti.Value())
	}
}

func TestTextInputCharLimit(t *testing.T) {
	ti := NewTextInput().Focus()
	ti.CharLimit = 3
	ti = typeKeys(ti, "보리차한잔")
	if ti.Value() != "보리차" {
		t.Errorf("= %q, 원하는 값 %q (룬 3개)", ti.Value(), "보리차")
	}
}

// 초점이 없으면 키를 안 받는다. 화면에 입력창이 여럿일 때 필요한 규칙이다.
func TestTextInputBlurred(t *testing.T) {
	ti := typeKeys(NewTextInput(), "abc")
	if ti.Value() != "" {
		t.Errorf("초점 없이 입력됐다: %q", ti.Value())
	}
	ti = typeKeys(ti.Focus(), "abc")
	if ti.Value() != "abc" {
		t.Errorf("= %q", ti.Value())
	}
	if !ti.Focused() {
		t.Error("Focused() 가 거짓")
	}
	if typeKeys(ti.Blur(), "d").Value() != "abc" {
		t.Error("Blur 뒤에도 입력된다")
	}
}

// 붙여넣기는 커서 자리에 통째로 들어간다.
func TestTextInputPaste(t *testing.T) {
	ti := typeKeys(NewTextInput().Focus(), "ab")
	ti = press(ti, "left")
	ti, _ = ti.Update(tea.PasteMsg("보리차"))
	if ti.Value() != "a보리차b" {
		t.Errorf("= %q", ti.Value())
	}
}

func TestTextInputSetValueAndReset(t *testing.T) {
	ti := NewTextInput().Focus().SetValue("보리차")
	if ti.Value() != "보리차" || ti.Position() != 3 {
		t.Errorf("SetValue = %q, 커서 %d", ti.Value(), ti.Position())
	}
	ti = ti.Reset()
	if ti.Value() != "" || ti.Position() != 0 {
		t.Errorf("Reset 뒤 = %q, 커서 %d", ti.Value(), ti.Position())
	}
}

// 화면 폭은 언제나 프롬프트 + Width 다. 글이 길어도, 한글이 섞여도.
// 이게 어긋나면 입력창 옆에 놓인 것이 전부 밀린다.
func TestTextInputViewWidthIsStable(t *testing.T) {
	ti := NewTextInput().Focus()
	ti.Prompt = "> "
	ti.Width = 10
	want := width.StringWidth(ti.Prompt) + 10
	for _, s := range []string{"", "a", "보리차", "보리차 한 잔 더 주세요", "abcdefghijklmnop", "한a한a한a한a한a"} {
		v := ti.SetValue(s)
		if got := width.StringWidth(v.View()); got != want {
			t.Errorf("값 %q 일 때 %d칸, 원하는 값 %d칸: %q", s, got, want, v.View())
		}
	}
}

// 글이 폭보다 길면 옆으로 밀린다. 커서는 언제나 보여야 한다.
func TestTextInputScrolls(t *testing.T) {
	ti := NewTextInput().Focus()
	ti.Prompt = ""
	ti.Width = 6
	ti = ti.SetValue("abcdefghij") // 커서는 끝(10)
	v := ti.View()
	if !strings.Contains(v, "fghij") {
		t.Errorf("끝이 안 보인다: %q", v)
	}
	ti = press(ti, "home")
	v = ti.View()
	if !strings.HasPrefix(strings.TrimLeft(v, " "), "abcde") {
		t.Errorf("home 뒤 앞부분이 안 보인다: %q", v)
	}
}

// 비어 있으면 안내 글을 보여 준다.
func TestTextInputPlaceholder(t *testing.T) {
	ti := NewTextInput()
	ti.Prompt = "> "
	ti.Width = 12
	ti.Placeholder = "할 일을 적으세요"
	if !strings.Contains(ti.View(), "할 일") {
		t.Errorf("안내 글이 안 보인다: %q", ti.View())
	}
	if got := width.StringWidth(ti.View()); got != 14 {
		t.Errorf("안내 글일 때 %d칸, 원하는 값 14칸", got)
	}
	if strings.Contains(ti.SetValue("x").View(), "할 일") {
		t.Error("값이 있는데 안내 글이 남아 있다")
	}
}
