package widgets

import (
	"strings"

	"treasure/boricha/style"
	"treasure/boricha/width"
)

// Help 는 키 배치 목록을 도움말로 그린다.
//
// 짧은 형태는 화면 맨 아래에 늘 붙어 있는 한 줄이고, 전체 형태는 ? 를 눌렀을 때
// 펼쳐지는 표다. 둘 다 **같은 Binding 목록** 에서 나온다는 것이 요점이다 —
// 도움말과 실제 동작이 어긋날 자리가 없다.
type Help struct {
	// ShowAll 이 참이면 세로로 펼친 표, 거짓이면 한 줄.
	ShowAll bool
	// Width 가 0보다 크면 그 폭을 넘지 않게 잘라 낸다.
	Width int
	// Separator 는 한 줄 도움말에서 항목 사이에 넣을 것.
	Separator string

	KeyStyle  style.Style
	DescStyle style.Style
	SepStyle  style.Style
}

func NewHelp() Help {
	return Help{
		Separator: " • ",
		DescStyle: style.New().Faint(true),
		SepStyle:  style.New().Faint(true),
	}
}

// Profile 은 세 스타일의 색 수준을 한꺼번에 맞춘 복사본을 돌려준다.
// 프로그램이 ColorProfileMsg 를 받은 자리에서 한 번 부르면 된다.
func (h Help) Profile(p style.Profile) Help {
	h.KeyStyle = h.KeyStyle.Profile(p)
	h.DescStyle = h.DescStyle.Profile(p)
	h.SepStyle = h.SepStyle.Profile(p)
	return h
}

// View 는 도움말을 그린다. 꺼 둔 배치는 건너뛴다 —
// 쓸 수 없는 키를 알려 주는 것은 거짓말이다.
func (h Help) View(bs []Binding) string {
	var on []Binding
	for _, b := range bs {
		if b.Enabled() && b.Help[0] != "" {
			on = append(on, b)
		}
	}
	if len(on) == 0 {
		return ""
	}
	if h.ShowAll {
		return h.full(on)
	}
	return h.short(on)
}

func (h Help) short(bs []Binding) string {
	parts := make([]string, 0, len(bs))
	for _, b := range bs {
		parts = append(parts, h.KeyStyle.Render(b.Help[0])+" "+h.DescStyle.Render(b.Help[1]))
	}
	out := strings.Join(parts, h.SepStyle.Render(h.Separator))
	if h.Width > 0 {
		out = width.Truncate(out, h.Width)
	}
	return out
}

// full 은 키 칸의 폭을 맞춰 세로로 늘어놓는다.
// 폭을 맞추지 않으면 설명이 들쭉날쭉해서 표로 안 읽힌다.
func (h Help) full(bs []Binding) string {
	kw, dw := 0, 0
	for _, b := range bs {
		if w := width.StringWidth(b.Help[0]); w > kw {
			kw = w
		}
		if w := width.StringWidth(b.Help[1]); w > dw {
			dw = w
		}
	}
	lines := make([]string, 0, len(bs))
	for _, b := range bs {
		key := h.KeyStyle.Render(width.Pad(b.Help[0], kw))
		desc := h.DescStyle.Render(width.Pad(b.Help[1], dw))
		line := key + " " + desc
		if h.Width > 0 {
			line = width.Truncate(line, h.Width)
		}
		lines = append(lines, line)
	}
	return strings.Join(lines, "\n")
}
