// Package render 는 View() 가 만든 문자열을 터미널이 실제로 받아야 할 바이트로 바꾼다.
//
// 이 층이 없어도 화면은 그릴 수 있다. 매 프레임 화면을 지우고 처음부터 다시 쓰면 된다.
// 다만 그러면 깜빡인다 — 지운 순간과 다시 그린 순간 사이에 터미널이 화면을 한 번
// 보여 주면, 사람 눈에 검은 화면이 스친다. 이 패키지의 존재 이유는 그 틈을 없애는 것이다.
package render

import (
	"strings"

	"treasure/boricha/width"
)

// Frame 은 "화면에 보일 줄들" 이다. View() 가 준 문자열을 화면 크기에 맞춰 자른 것.
type Frame struct{ Lines []string }

// NewFrame 은 View 문자열을 w칸 × h줄 화면에 맞춰 자른다.
//
// **자르는 것이 이 함수의 요점이다.** 폭을 넘는 줄을 그냥 내보내면 터미널이 스스로
// 다음 줄로 감아 버린다. 그러면 우리가 세는 줄 번호와 화면의 실제 줄 번호가 어긋나고,
// 줄 번호로 커서를 옮기는 렌더러가 그때부터 엉뚱한 줄을 고쳐 쓴다.
// 터미널 UI 에서 화면이 무너지는 가장 흔한 원인이 이것이다.
//
// 자를 때는 width.Truncate 를 쓴다. 한글을 반 칸으로 자를 수 없고, 꾸밈 시퀀스는
// 칸을 안 먹으므로 세지 않는다.
func NewFrame(view string, w, h int) Frame {
	lines := strings.Split(view, "\n")
	if h > 0 && len(lines) > h {
		lines = lines[:h]
	}
	if w > 0 {
		for i, l := range lines {
			if width.StringWidth(l) > w {
				lines[i] = width.Truncate(l, w)
			}
		}
	}
	return Frame{Lines: lines}
}

// Line 은 i번째 줄을 돌려준다. 없는 줄은 빈 줄이다.
//
// 범위를 넘겨도 죽지 않는 것이 중요하다. 화면이 줄어들면 diff 가 "지난 프레임에는
// 있었지만 이번에는 없는 줄" 을 물어보게 되는데, 그것이 정상적인 흐름이다.
func (f Frame) Line(i int) string {
	if i < 0 || i >= len(f.Lines) {
		return ""
	}
	return f.Lines[i]
}

func (f Frame) Height() int { return len(f.Lines) }
