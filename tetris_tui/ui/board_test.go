package ui

import (
	"strings"
	"testing"

	"charm.land/lipgloss/v2"

	"treasure/tetris_tui/core"
)

// 블록 문자는 반드시 두 칸이어야 한다. 한 칸이면 판이 세로로 길쭉해지고,
// 세 칸이면 테두리가 어긋난다. 이 덱의 렌더링 전체가 이 전제 위에 서 있다.
func TestEveryCellGlyphIsTwoColumnsWide(t *testing.T) {
	for name, s := range map[string]string{"Cell": Cell, "GhostCell": GhostCell, "EmptyCell": EmptyCell} {
		if w := lipgloss.Width(s); w != 2 {
			t.Errorf("%s(%q)의 폭이 %d 다 — 2 여야 한다", name, s, w)
		}
	}
}

func newBoardLayers() (cells, overlay []uint8) {
	return make([]uint8, core.Vis*core.W), make([]uint8, core.Vis*core.W)
}

// 판의 크기는 상수와 정확히 같아야 한다. 레이아웃 계산이 전부 이 값을 쓴다.
func TestRenderedBoardMatchesItsDeclaredSize(t *testing.T) {
	cells, overlay := newBoardLayers()
	got := RenderBoard(cells, overlay, "", false)
	w, h := lipgloss.Size(got)
	if w != BoardWidth {
		t.Errorf("판 폭이 %d — 상수는 %d 다", w, BoardWidth)
	}
	if h != BoardHeight {
		t.Errorf("판 높이가 %d — 상수는 %d 다", h, BoardHeight)
	}
}

// 제목을 붙여도 폭은 그대로여야 한다(테두리 위에 얹는다).
func TestTitleDoesNotChangeTheWidth(t *testing.T) {
	cells, overlay := newBoardLayers()
	plain := RenderBoard(cells, overlay, "", false)
	titled := RenderBoard(cells, overlay, "1P", false)
	if lipgloss.Width(plain) != lipgloss.Width(titled) {
		t.Errorf("제목을 붙이니 폭이 %d → %d 로 바뀌었다",
			lipgloss.Width(plain), lipgloss.Width(titled))
	}
	if !strings.Contains(titled, "1P") {
		t.Error("제목이 안 보인다")
	}
}

// 현재 조각은 고스트를 덮어 그린다. 같은 칸에 둘 다 있으면 조각이 이긴다.
func TestOverlayCoversCells(t *testing.T) {
	cells, overlay := newBoardLayers()
	cells[0] = 1
	overlay[0] = 3 // 현재 조각
	got := RenderBoard(cells, overlay, "", false)
	if !strings.Contains(got, Cell) {
		t.Error("블록이 하나도 안 그려졌다")
	}
	// 오버레이가 비어 있으면 굳은 블록이 보이고, 채워져 있으면 그 색이 이긴다.
	// 색까지 문자열로 비교하면 깨지기 쉬우므로 "그림이 달라진다"만 확인한다.
	overlay[0] = 0
	if RenderBoard(cells, overlay, "", false) == got {
		t.Error("오버레이가 있든 없든 그림이 같다")
	}
}

// 고스트는 현재 조각과 다른 글자로 그린다.
func TestGhostUsesItsOwnGlyph(t *testing.T) {
	cells, overlay := newBoardLayers()
	overlay[0] = 8 // 고스트(조각 0)
	got := RenderBoard(cells, overlay, "", false)
	if !strings.Contains(got, GhostCell) {
		t.Errorf("고스트 글자가 안 보인다:\n%s", got)
	}
}

// 빈 판에는 블록이 하나도 없어야 한다.
func TestEmptyBoardHasNoBlocks(t *testing.T) {
	cells, overlay := newBoardLayers()
	got := RenderBoard(cells, overlay, "", false)
	if strings.Contains(got, Cell) {
		t.Errorf("빈 판에 블록이 있다:\n%s", got)
	}
}

// 게임 오버 표시는 크기를 바꾸지 않아야 한다 — 옆의 패널이 어긋난다.
func TestGameOverKeepsTheSize(t *testing.T) {
	cells, overlay := newBoardLayers()
	a := RenderBoard(cells, overlay, "1P", false)
	b := RenderBoard(cells, overlay, "1P", true)
	aw, ah := lipgloss.Size(a)
	bw, bh := lipgloss.Size(b)
	if aw != bw || ah != bh {
		t.Errorf("게임 오버 표시가 판 크기를 %d×%d → %d×%d 로 바꿨다", aw, ah, bw, bh)
	}
}

// 층의 길이가 모자라도 죽지 않아야 한다. 화면 코드는 게임을 멈출 권리가 없다.
func TestShortLayersDoNotPanic(t *testing.T) {
	got := RenderBoard(nil, nil, "", false)
	if lipgloss.Height(got) != BoardHeight {
		t.Errorf("빈 층으로 그린 판의 높이가 %d 다", lipgloss.Height(got))
	}
}

// 미리보기 조각은 2줄 × 8칸이다. 스폰 상태의 일곱 조각이 전부 여기에 들어간다.
func TestMiniPieceSize(t *testing.T) {
	for p := 0; p < core.PieceCount; p++ {
		got := MiniPiece(p)
		w, h := lipgloss.Size(got)
		if w != 8 || h != 2 {
			t.Errorf("%s 미리보기가 %d×%d 다 — 8×2 여야 한다", core.PieceNames[p], w, h)
		}
		if !strings.Contains(got, Cell) {
			t.Errorf("%s 미리보기에 블록이 없다", core.PieceNames[p])
		}
	}
}

// 조각이 없을 때(홀드 빈 칸)도 같은 크기의 빈 자리를 내야 레이아웃이 안 흔들린다.
func TestMiniPieceOfNothing(t *testing.T) {
	got := MiniPiece(-1)
	w, h := lipgloss.Size(got)
	if w != 8 || h != 2 {
		t.Errorf("빈 미리보기가 %d×%d 다", w, h)
	}
	if strings.Contains(got, Cell) {
		t.Error("빈 미리보기에 블록이 있다")
	}
}

// 최소 크기는 실제 렌더 결과보다 작으면 안 된다 — 작게 잡으면 화면이 잘린다.
func TestMinSizeFitsTheRealLayout(t *testing.T) {
	w, h := MinSize(1)
	if w < BoardWidth+PanelWidth {
		t.Errorf("1인용 최소 폭이 %d — 판 %d + 패널 %d 는 되어야 한다",
			w, BoardWidth, PanelWidth)
	}
	if h < BoardHeight {
		t.Errorf("1인용 최소 높이가 %d — 판 높이가 %d 다", h, BoardHeight)
	}
	w2, _ := MinSize(2)
	if w2 < BoardWidth*2+PanelWidth {
		t.Errorf("2인용 최소 폭이 %d — 판 둘 + 패널은 %d 다", w2, BoardWidth*2+PanelWidth)
	}
	if w2 <= w {
		t.Error("2인용이 1인용보다 넓지 않다")
	}
}
