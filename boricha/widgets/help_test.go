package widgets

import (
	"strings"
	"testing"

	"treasure/boricha/style"
	"treasure/boricha/width"
)

func bindings() []Binding {
	return []Binding{
		NewBinding("↑/k", "위로", "up", "k"),
		NewBinding("↓/j", "아래로", "down", "j"),
		NewBinding("enter", "고르기", "enter"),
		NewBinding("q", "끝내기", "q", "ctrl+c"),
	}
}

// 짧은 도움말은 한 줄이다. 화면 맨 아래에 늘 붙어 있는 그 줄.
func TestHelpShort(t *testing.T) {
	h := NewHelp()
	got := h.View(bindings())
	want := "↑/k 위로 • ↓/j 아래로 • enter 고르기 • q 끝내기"
	if got != want {
		t.Errorf("= %q\n원하는 값 %q", got, want)
	}
}

// 꺼 둔 배치는 도움말에도 안 나온다. 쓸 수 없는 키를 알려 주면 거짓말이 된다.
func TestHelpSkipsDisabled(t *testing.T) {
	bs := bindings()
	bs[2] = bs[2].SetEnabled(false)
	got := NewHelp().View(bs)
	if strings.Contains(got, "고르기") {
		t.Errorf("꺼 둔 배치가 도움말에 있다: %q", got)
	}
}

// 폭이 모자라면 잘라 낸다. 도움말 줄이 화면을 넘으면 터미널이 감아 버려
// 우리가 세어 둔 줄 수가 어긋난다.
func TestHelpTruncatesToWidth(t *testing.T) {
	h := NewHelp()
	h.Width = 20
	got := h.View(bindings())
	if w := width.StringWidth(got); w > 20 {
		t.Errorf("도움말이 %d칸 — 20칸을 넘는다: %q", w, got)
	}
}

// 전체 도움말은 줄마다 하나씩 세로로 늘어놓는다.
func TestHelpFull(t *testing.T) {
	h := NewHelp()
	h.ShowAll = true
	got := h.View(bindings())
	lines := strings.Split(got, "\n")
	if len(lines) != 4 {
		t.Fatalf("줄이 %d개, 원하는 값 4개: %q", len(lines), got)
	}
	if !strings.Contains(lines[0], "위로") || !strings.Contains(lines[3], "끝내기") {
		t.Errorf("내용 = %q", got)
	}
	// 키 칸의 폭을 맞춰 세로줄이 보이게 한다.
	w0 := width.StringWidth(lines[0])
	for i, l := range lines {
		if width.StringWidth(l) != w0 {
			t.Errorf("줄 %d 의 폭이 %d, 첫 줄은 %d", i, width.StringWidth(l), w0)
		}
	}
}

func TestHelpEmpty(t *testing.T) {
	if got := NewHelp().View(nil); got != "" {
		t.Errorf("= %q, 원하는 값 \"\"", got)
	}
}

// 색을 켜면 키와 설명이 다른 색으로 나온다.
func TestHelpStyled(t *testing.T) {
	h := NewHelp().Profile(style.ANSI)
	got := h.View(bindings()[:1])
	if !strings.Contains(got, "\x1b[") {
		t.Errorf("색을 켰는데 시퀀스가 없다: %q", got)
	}
}
