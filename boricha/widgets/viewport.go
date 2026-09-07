package widgets

import (
	"strings"

	"treasure/boricha/style"
	"treasure/boricha/tea"
	"treasure/boricha/width"
)

// 마우스 휠 한 번에 몇 줄을 움직일까. 3줄은 대부분의 터미널·브라우저가 쓰는 값이다.
const wheelLines = 3

// Viewport 는 긴 글을 창만큼만 보여 주고 위아래로 움직이는 부품이다.
//
// 내용을 넣을 때 폭에 맞춰 미리 접어 둔다. 접지 않고 그리면 긴 줄을 터미널이 스스로
// 감아 버려, 우리가 "3줄" 이라고 생각한 화면이 실제로는 5줄이 된다.
// 그 순간 렌더러의 줄 번호가 어긋나고 화면이 무너진다.
type Viewport struct {
	Width, Height int
	// YOffset 은 맨 위에 보이는 줄의 번호(접힌 뒤 기준).
	YOffset int
	Style   style.Style

	lines []string
}

func NewViewport(w, h int) Viewport { return Viewport{Width: w, Height: h} }

// SetContent 는 보여 줄 글을 넣는다. 폭에 맞춰 접고, 스크롤 위치를 다시 잡는다.
func (v Viewport) SetContent(s string) Viewport {
	v.lines = width.Wrap(s, v.Width)
	return v.clamp()
}

func (v Viewport) TotalLines() int { return len(v.lines) }

// maxOffset 은 더 내려갈 수 없는 자리다. 내용이 화면보다 짧으면 0이다.
func (v Viewport) maxOffset() int {
	if n := len(v.lines) - v.Height; n > 0 {
		return n
	}
	return 0
}

func (v Viewport) clamp() Viewport {
	if v.YOffset > v.maxOffset() {
		v.YOffset = v.maxOffset()
	}
	if v.YOffset < 0 {
		v.YOffset = 0
	}
	return v
}

func (v Viewport) AtTop() bool    { return v.YOffset <= 0 }
func (v Viewport) AtBottom() bool { return v.YOffset >= v.maxOffset() }

// ScrollPercent 는 0(맨 위)에서 1(맨 아래) 사이의 값이다.
// 내용이 화면보다 짧으면 1이다 — 다 보이고 있으니 "끝까지 봤다" 가 맞다.
func (v Viewport) ScrollPercent() float64 {
	if v.maxOffset() == 0 {
		return 1
	}
	return float64(v.YOffset) / float64(v.maxOffset())
}

func (v Viewport) LineDown(n int) Viewport { v.YOffset += n; return v.clamp() }
func (v Viewport) LineUp(n int) Viewport   { v.YOffset -= n; return v.clamp() }
func (v Viewport) GotoTop() Viewport       { v.YOffset = 0; return v }
func (v Viewport) GotoBottom() Viewport    { v.YOffset = v.maxOffset(); return v }

// KeyBindings 는 이 부품이 받아들이는 키와 그 설명이다.
// 도움말 줄이 이 목록을 그대로 그리므로, 키를 바꾸면 도움말도 같이 바뀐다.
func (v Viewport) KeyBindings() []Binding {
	return []Binding{
		NewBinding("↑/k", "한 줄 위로", "up", "k"),
		NewBinding("↓/j", "한 줄 아래로", "down", "j"),
		NewBinding("pgup/b", "한 화면 위로", "pgup", "b"),
		NewBinding("pgdn/f", "한 화면 아래로", "pgdown", "f", " "),
		NewBinding("home/g", "맨 위로", "home", "g"),
		NewBinding("end/G", "맨 아래로", "end", "G"),
	}
}

func (v Viewport) Update(msg tea.Msg) (Viewport, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.KeyMsg:
		switch msg.String() {
		case "up", "k":
			return v.LineUp(1), nil
		case "down", "j":
			return v.LineDown(1), nil
		case "pgup", "b":
			return v.LineUp(v.Height), nil
		case "pgdown", "f", "space":
			return v.LineDown(v.Height), nil
		case "home", "g":
			return v.GotoTop(), nil
		case "end", "G":
			return v.GotoBottom(), nil
		}
	case tea.MouseMsg:
		switch msg.Button {
		case tea.MouseWheelUp:
			return v.LineUp(wheelLines), nil
		case tea.MouseWheelDown:
			return v.LineDown(wheelLines), nil
		}
	}
	return v, nil
}

// View 는 언제나 정확히 Height 줄, Width 칸을 돌려준다.
// 내용이 모자라면 빈 줄로 채운다 — 모양이 흔들리면 옆에 놓인 것이 전부 밀린다.
func (v Viewport) View() string {
	out := make([]string, 0, v.Height)
	for i := 0; i < v.Height; i++ {
		s := ""
		if n := v.YOffset + i; n >= 0 && n < len(v.lines) {
			s = v.lines[n]
		}
		out = append(out, v.Style.Render(width.Pad(width.Truncate(s, v.Width), v.Width)))
	}
	return strings.Join(out, "\n")
}
