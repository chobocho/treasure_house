package ui

import (
	"strings"

	"treasure/tetris_tui/core"
)

// 판 하나가 차지하는 칸 수(테두리 포함).
// 레이아웃 계산이 전부 이 두 상수를 쓴다 — 숫자를 여기저기 흩어 놓으면
// 테두리를 한 번 바꿀 때마다 화면이 어긋난다.
const (
	BoardWidth  = core.W*2 + 2
	BoardHeight = core.Vis + 2
)

// RenderBoard 는 굳은 블록 층과 오버레이 층을 겹쳐 판 하나를 그린다.
//
//	cells   : 굳은 블록 (Vis*W)
//	overlay : 1~7 현재 조각 · 8~14 고스트 (Vis*W)
//	title   : 위쪽 테두리에 새길 이름 ("1P", "AI" …). 빈 문자열이면 안 새긴다.
//	over    : 게임 오버면 테두리를 빨갛게
//
// 테두리를 lipgloss 의 Border 로 두르지 않고 직접 그리는 이유는 **제목** 때문이다.
// 위쪽 테두리 한가운데에 이름을 새기려면 그 줄을 우리가 만들어야 한다.
// 그리고 직접 그리면 폭이 정확히 BoardWidth 라는 것을 눈으로 확인할 수 있다.
func RenderBoard(cells, overlay []uint8, title string, over bool) string {
	inner := core.W * 2
	bs := BorderStyle
	if over {
		bs = OverStyle
	}

	var b strings.Builder
	b.WriteString(bs.Render(topBorder(inner, title)))
	b.WriteByte('\n')

	var row strings.Builder
	for y := 0; y < core.Vis; y++ {
		row.Reset()
		for x := 0; x < core.W; x++ {
			i := y*core.W + x
			v := at(cells, i)
			if o := at(overlay, i); o != 0 {
				if o >= 8 {
					// 고스트. 색은 조각 색을 그대로 쓰되 흐리게, 글자는 다르게.
					row.WriteString(CellStyle(o-7, true).Render(GhostCell))
					continue
				}
				v = o
			}
			if v == 0 {
				row.WriteString(EmptyCell)
				continue
			}
			row.WriteString(CellStyle(v, false).Render(Cell))
		}
		b.WriteString(bs.Render("│") + row.String() + bs.Render("│"))
		b.WriteByte('\n')
	}

	b.WriteString(bs.Render("╰" + strings.Repeat("─", inner) + "╯"))
	return b.String()
}

// at 은 층이 짧거나 nil 이어도 안전하게 읽는다.
// 화면 코드는 게임을 멈출 권리가 없다 — 데이터가 모자라면 빈칸으로 그린다.
func at(layer []uint8, i int) uint8 {
	if i < 0 || i >= len(layer) {
		return 0
	}
	return layer[i]
}

// topBorder 는 제목을 새긴 위쪽 테두리를 만든다. 폭은 언제나 inner + 2 다.
func topBorder(inner int, title string) string {
	if title == "" {
		return "╭" + strings.Repeat("─", inner) + "╮"
	}
	label := " " + title + " "
	n := runeCells(label)
	if n > inner-2 {
		// 제목이 너무 길면 잘라 낸다. 폭이 흔들리는 것보다 이름이 잘리는 편이 낫다.
		label = label[:0]
		n = 0
	}
	left := 1
	right := inner - n - left
	if right < 0 {
		right = 0
	}
	return "╭" + strings.Repeat("─", left) + label + strings.Repeat("─", right) + "╮"
}

// runeCells 는 문자열이 차지하는 화면 칸 수를 센다.
// 여기서는 제목에 ASCII 와 한글만 쓰므로 한글을 2칸으로 세는 것으로 충분하다.
// (일반적인 폭 계산이 필요하면 lipgloss.Width 를 쓴다 — 여기서 안 쓰는 이유는
//
//	테두리 계산이 lipgloss 스타일을 거치기 전의 **순수 문자열**을 다루기 때문이다)
func runeCells(s string) int {
	n := 0
	for _, r := range s {
		if r >= 0x1100 {
			n += 2
			continue
		}
		n++
	}
	return n
}

// MiniPiece 는 다음·홀드 칸에 쓰는 작은 조각 그림. 2줄 × 8칸이다.
//
// 스폰 회전 상태(rot 0)의 일곱 조각은 전부 4×2 상자에 들어간다 —
// I 조각조차 가로로 누워 있어서 두 줄이면 충분하다. 그래서 미리보기 높이가
// 조각마다 달라지는 일이 없고, 패널의 높이가 흔들리지 않는다.
//
// piece 가 범위 밖이면(홀드가 비었을 때의 -1 포함) 같은 크기의 빈 자리를 낸다.
func MiniPiece(piece int) string {
	var b strings.Builder
	var m uint16
	if piece >= 0 && piece < core.PieceCount {
		m = core.Shapes[piece][0]
	}
	for y := 0; y < 2; y++ {
		if y > 0 {
			b.WriteByte('\n')
		}
		for x := 0; x < 4; x++ {
			if m&(1<<uint(y*4+x)) != 0 {
				b.WriteString(CellStyle(uint8(piece+1), false).Render(Cell))
				continue
			}
			b.WriteString(EmptyCell)
		}
	}
	return b.String()
}

// MinSize 는 자리 수에 따른 최소 터미널 크기.
//
// 실제 레이아웃에서 계산한다 — 넉넉하게 잡아 두면 멀쩡한 크기에서도
// "터미널을 키워 주세요"가 뜨고, 빠듯하게 잡으면 화면이 잘린다.
// 높이의 +2 는 도움말 한 줄과 여유 한 줄이다.
func MinSize(seats int) (w, h int) {
	if seats < 1 {
		seats = 1
	}
	return BoardWidth*seats + PanelWidth, BoardHeight + 2
}
