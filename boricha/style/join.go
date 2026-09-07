package style

import (
	"strings"

	"treasure/boricha/width"
)

// JoinHorizontal 은 덩어리들을 나란히 붙인다.
//
// 높이가 다르면 짧은 쪽에 빈 줄을 채우는데, pos 가 그 빈 줄을 위에 둘지 아래에 둘지 정한다.
// 폭을 세는 데 width.StringWidth 를 쓴다는 것이 핵심이다 — 한글이 든 덩어리를
// len() 으로 세면 옆 덩어리가 통째로 밀린다. 5부의 폭 표가 여기서 값을 한다.
func JoinHorizontal(pos Position, blocks ...string) string {
	if len(blocks) == 0 {
		return ""
	}
	if len(blocks) == 1 {
		return blocks[0]
	}

	cols := make([][]string, len(blocks))
	height := 0
	for i, b := range blocks {
		lines := strings.Split(b, "\n")
		w := 0
		for _, l := range lines {
			if x := width.StringWidth(l); x > w {
				w = x
			}
		}
		for j, l := range lines {
			lines[j] = width.Pad(l, w)
		}
		cols[i] = lines
		if len(lines) > height {
			height = len(lines)
		}
	}
	for i, lines := range cols {
		if len(lines) == height {
			continue
		}
		blank := strings.Repeat(" ", width.StringWidth(lines[0]))
		cols[i] = alignV(lines, height, blank, pos)
	}

	out := make([]string, height)
	var b strings.Builder
	for y := 0; y < height; y++ {
		b.Reset()
		for _, lines := range cols {
			b.WriteString(lines[y])
		}
		out[y] = b.String()
	}
	return strings.Join(out, "\n")
}

// JoinVertical 은 덩어리들을 위아래로 쌓는다. 폭이 다르면 가장 넓은 것에 맞춘다.
func JoinVertical(pos Position, blocks ...string) string {
	var lines []string
	w := 0
	for _, b := range blocks {
		for _, l := range strings.Split(b, "\n") {
			lines = append(lines, l)
			if x := width.StringWidth(l); x > w {
				w = x
			}
		}
	}
	for i, l := range lines {
		lines[i] = alignH(l, w, pos)
	}
	return strings.Join(lines, "\n")
}

// Place 는 덩어리를 w×h 칸 안에 놓는다. 화면 한가운데에 상자를 띄울 때 쓴다.
// 덩어리가 이미 그보다 크면 그대로 둔다 — 잘라 내는 것은 렌더러의 일이다.
func Place(w, h int, hpos, vpos Position, s string) string {
	lines := strings.Split(s, "\n")
	bw := 0
	for _, l := range lines {
		if x := width.StringWidth(l); x > bw {
			bw = x
		}
	}
	if w > bw {
		bw = w
	}
	for i, l := range lines {
		lines[i] = alignH(l, bw, hpos)
	}
	lines = alignV(lines, h, strings.Repeat(" ", bw), vpos)
	return strings.Join(lines, "\n")
}
