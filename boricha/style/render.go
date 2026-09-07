package style

import (
	"strings"

	"treasure/boricha/width"
)

// Render 는 스타일을 글에 입혀 완성된 문자열을 만든다.
//
// 순서가 전부다. 이 순서를 한 번 정해 두면 "패딩이 테두리 안인가 밖인가" 같은 질문에
// 매번 답할 필요가 없다:
//
//  1. 조각들을 공백으로 잇는다
//  2. 폭이 정해져 있으면 그 폭에 맞춰 접는다
//  3. 줄마다 남는 자리를 정렬 방향으로 채워 직사각형으로 만든다
//  4. 패딩을 두른다 (좌우는 공백, 위아래는 빈 줄)
//  5. 높이가 정해져 있으면 빈 줄로 채운다
//  6. 줄마다 꾸밈 시퀀스를 씌운다 ← 배경색이 패딩까지 덮는 지점
//  7. 테두리를 두른다
//  8. 여백을 두른다 ← 배경색이 여기는 안 닿는다
//
// 결과의 모든 줄은 폭이 같다. 그래야 이 덩어리를 다른 덩어리와 나란히 붙일 수 있다.
func (s Style) Render(parts ...string) string {
	text := strings.Join(parts, " ")

	// 1~2. 접기
	inner := s.width - s.padLeft - s.padRight
	var lines []string
	if s.width > 0 {
		if inner < 1 {
			inner = 1
		}
		lines = width.Wrap(text, inner)
	} else {
		lines = strings.Split(text, "\n")
	}

	// 3. 직사각형으로
	blockW := inner
	if s.width == 0 {
		blockW = 0
		for _, l := range lines {
			if w := width.StringWidth(l); w > blockW {
				blockW = w
			}
		}
	}
	for i, l := range lines {
		lines[i] = alignH(l, blockW, s.align)
	}

	// 4. 패딩
	if s.padLeft > 0 || s.padRight > 0 {
		lp, rp := strings.Repeat(" ", s.padLeft), strings.Repeat(" ", s.padRight)
		for i := range lines {
			lines[i] = lp + lines[i] + rp
		}
	}
	full := blockW + s.padLeft + s.padRight
	blank := strings.Repeat(" ", full)
	for i := 0; i < s.padTop; i++ {
		lines = append([]string{blank}, lines...)
	}
	for i := 0; i < s.padBottom; i++ {
		lines = append(lines, blank)
	}

	// 5. 높이 맞추기
	lines = alignV(lines, s.height, blank, s.valign)

	// 6. 꾸밈. 줄마다 열고 닫는다.
	//
	// 왜 줄마다인가. 한 번 열고 마지막에 닫으면 바이트는 줄지만, 줄 단위 diff 렌더러가
	// 가운데 줄 하나만 다시 그릴 때 그 줄에 여는 시퀀스가 없어 색이 사라진다.
	// "줄 하나는 그 자체로 완결" 이 우리 렌더러의 전제다.
	if sgr := s.sgr(); sgr != "" {
		for i := range lines {
			lines[i] = sgr + lines[i] + reset
		}
	}

	// 7. 테두리
	if s.hasBorder {
		lines = s.drawBorder(lines, full)
		full += boolInt(s.bordLeft) + boolInt(s.bordRight)
	}

	// 8. 여백
	if s.marLeft > 0 || s.marRight > 0 {
		lm, rm := strings.Repeat(" ", s.marLeft), strings.Repeat(" ", s.marRight)
		for i := range lines {
			lines[i] = lm + lines[i] + rm
		}
		full += s.marLeft + s.marRight
	}
	mblank := strings.Repeat(" ", full)
	for i := 0; i < s.marTop; i++ {
		lines = append([]string{mblank}, lines...)
	}
	for i := 0; i < s.marBottom; i++ {
		lines = append(lines, mblank)
	}

	return strings.Join(lines, "\n")
}

const reset = "\x1b[0m"

// sgr 은 이 스타일의 꾸밈을 한 시퀀스로 모은다.
// 꾸밈 → 글자색 → 배경색 순서. 나눠 보내도 결과는 같지만 한 번에 보내면 바이트가 줄고
// 캡처를 눈으로 읽기도 쉽다.
func (s Style) sgr() string {
	if s.profile == NoColor {
		return ""
	}
	var p []string
	for _, a := range []struct {
		on   bool
		code string
	}{
		{s.bold, "1"}, {s.faint, "2"}, {s.italic, "3"},
		{s.underline, "4"}, {s.reverse, "7"}, {s.strike, "9"},
	} {
		if a.on {
			p = append(p, a.code)
		}
	}
	if c := s.profile.fgParams(s.fg); c != "" {
		p = append(p, c)
	}
	if c := s.profile.bgParams(s.bg); c != "" {
		p = append(p, c)
	}
	if len(p) == 0 {
		return ""
	}
	return "\x1b[" + strings.Join(p, ";") + "m"
}

// drawBorder 는 이미 직사각형이 된 줄들을 테두리로 감싼다.
//
// 모서리는 맞닿는 두 변이 다 있을 때만 그린다. 위쪽만 그리라고 했는데 모서리가 나오면
// 그것은 "ㄱ" 자 조각이지 테두리가 아니다.
func (s Style) drawBorder(lines []string, inner int) []string {
	bs := ""
	if c := s.profile.fgParams(s.borderFg); c != "" {
		bs = "\x1b[" + c + "m"
	}
	paint := func(str string) string {
		if bs == "" || str == "" {
			return str
		}
		return bs + str + reset
	}

	out := make([]string, 0, len(lines)+2)
	if s.bordTop {
		mid := strings.Repeat(s.border.Top, inner)
		l, r := "", ""
		if s.bordLeft {
			l = s.border.TopLeft
		}
		if s.bordRight {
			r = s.border.TopRight
		}
		out = append(out, paint(l+mid+r))
	}
	l, r := "", ""
	if s.bordLeft {
		l = paint(s.border.Left)
	}
	if s.bordRight {
		r = paint(s.border.Right)
	}
	for _, line := range lines {
		out = append(out, l+line+r)
	}
	if s.bordBottom {
		mid := strings.Repeat(s.border.Bottom, inner)
		bl, br := "", ""
		if s.bordLeft {
			bl = s.border.BottomLeft
		}
		if s.bordRight {
			br = s.border.BottomRight
		}
		out = append(out, paint(bl+mid+br))
	}
	return out
}

// alignH 는 한 줄을 w칸으로 만들되, 남는 자리를 pos 쪽으로 몬다.
func alignH(line string, w int, pos Position) string {
	gap := w - width.StringWidth(line)
	if gap <= 0 {
		return line
	}
	left := int(float64(gap) * float64(pos))
	return strings.Repeat(" ", left) + line + strings.Repeat(" ", gap-left)
}

// alignV 는 줄 묶음을 h줄로 만들되, 남는 줄을 pos 쪽으로 몬다.
func alignV(lines []string, h int, blank string, pos Position) []string {
	gap := h - len(lines)
	if gap <= 0 {
		return lines
	}
	top := int(float64(gap) * float64(pos))
	out := make([]string, 0, h)
	for i := 0; i < top; i++ {
		out = append(out, blank)
	}
	out = append(out, lines...)
	for i := 0; i < gap-top; i++ {
		out = append(out, blank)
	}
	return out
}

func boolInt(b bool) int {
	if b {
		return 1
	}
	return 0
}
