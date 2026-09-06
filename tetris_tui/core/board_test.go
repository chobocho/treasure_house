package core

import (
	"strings"
	"testing"
)

func rep(row string, n int) []string {
	out := make([]string, n)
	for i := range out {
		out[i] = row
	}
	return out
}

// Paint 는 그림의 **마지막 줄**을 판의 바닥줄에 놓는다.
// 이 방향을 헷갈리면 모든 테스트가 위아래 뒤집힌 판 위에서 돌게 된다.
func TestPaintPutsLastRowAtTheBottom(t *testing.T) {
	var b Board
	b.Paint([]string{"##########", ".........."})
	if b.At(0, H-1) != 0 {
		t.Error("마지막 줄(빈 줄)이 바닥에 안 놓였다")
	}
	if b.At(0, H-2) == 0 {
		t.Error("그 위 줄(꽉 찬 줄)이 비어 있다")
	}
	if b.At(0, 0) != 0 {
		t.Error("그림보다 위쪽이 안 지워졌다")
	}
}

func TestPaintMarksGarbageSeparately(t *testing.T) {
	var b Board
	b.Paint([]string{"#........X"})
	if got := b.At(0, H-1); got != Garbage {
		t.Errorf("'#' 이 %d 로 칠해졌다 — %d(가비지) 여야 한다", got, Garbage)
	}
	if got := b.At(9, H-1); got != 1 {
		t.Errorf("'X' 가 %d 로 칠해졌다 — 1 이어야 한다", got)
	}
}

// Paint 는 항상 판 전체를 먼저 지운다. 안 그러면 트레이스의 라운드 사이에
// 이전 판이 남아 두 구현이 갈라진다.
func TestPaintClearsFirst(t *testing.T) {
	var b Board
	b.Paint(rep("##########", 10))
	b.Paint([]string{".........."})
	if !b.Empty() {
		t.Error("두 번째 Paint 뒤에도 판이 안 비었다")
	}
}

func TestAtOutOfRangeIsZero(t *testing.T) {
	var b Board
	b.Paint(rep("##########", H))
	for _, c := range [][2]int{{-1, 0}, {W, 0}, {0, -1}, {0, H}} {
		if got := b.At(c[0], c[1]); got != 0 {
			t.Errorf("At(%d,%d) 이 %d 다 — 범위 밖은 0 이어야 한다", c[0], c[1], got)
		}
	}
}

// Collide 의 경계 규칙. 천장 위로 삐져나오는 건 합법이고, 바닥 아래는 아니다.
func TestCollideBoundaries(t *testing.T) {
	var b Board
	if b.Collide(PieceO, 0, 0, -4) {
		t.Error("천장 위(y=-4)가 충돌로 잡혔다 — 위로 삐져나오는 건 합법이다")
	}
	if !b.Collide(PieceO, 0, 0, H) {
		t.Error("바닥 아래가 충돌이 아니다")
	}
	if !b.Collide(PieceO, 0, -2, 0) {
		t.Error("왼쪽 벽 밖이 충돌이 아니다")
	}
	if !b.Collide(PieceO, 0, W, 0) {
		t.Error("오른쪽 벽 밖이 충돌이 아니다")
	}
}

func TestCollideWithLockedBlocks(t *testing.T) {
	var b Board
	b.Paint(rep("##########", 1))
	if !b.Collide(PieceO, 0, 0, H-2) {
		t.Error("바닥의 굳은 블록과 안 겹친다고 나온다")
	}
	if b.Collide(PieceO, 0, 0, H-3) {
		t.Error("한 칸 위인데 겹친다고 나온다")
	}
}

// Filled 는 Collide 와 경계 규칙이 **다르다**. 벽과 바닥은 막힌 것,
// 천장 위는 빈 것으로 센다. T스핀 판정이 이 차이 위에 서 있다.
func TestFilledTreatsWallsAsBlocked(t *testing.T) {
	var b Board
	if !b.Filled(-1, 5) || !b.Filled(W, 5) || !b.Filled(0, H) {
		t.Error("벽이나 바닥이 막힌 것으로 안 세어진다")
	}
	if b.Filled(0, -1) {
		t.Error("천장 위가 막힌 것으로 세어졌다")
	}
}

func TestDropY(t *testing.T) {
	var b Board
	// 빈 판: O 조각(아랫줄 인덱스 1)은 y+1 이 H 가 되는 자리에서 멈춘다.
	if got := b.DropY(PieceO, 0, 0, 0); got != H-2 {
		t.Errorf("빈 판에서 %d 에 멈췄다 — %d 를 기대했다", got, H-2)
	}
	b.Paint(rep("##########", 3))
	if got := b.DropY(PieceO, 0, 0, 0); got != H-5 {
		t.Errorf("3줄 쌓인 판에서 %d 에 멈췄다 — %d 를 기대했다", got, H-5)
	}
}

func TestClearLines(t *testing.T) {
	var b Board
	b.Paint([]string{"#########.", "##########", "##########", "#########."})
	n, mask := b.ClearLines()
	if n != 2 {
		t.Fatalf("지운 줄이 %d 다", n)
	}
	// 마스크 비트는 "지운 **순간**의 y"다 (y - Hidden).
	// 한 줄을 지우면 위가 내려오고 같은 y 를 다시 검사하므로, 붙어 있는 두 줄은
	// 둘 다 같은 자리(18번)에서 지워진다 — 비트가 하나만 선다.
	// 보기에는 어색하지만 C++ 원본이 그렇고, 여기서는 파리티가 우선이다.
	if mask != 1<<18 {
		t.Errorf("마스크가 %b 다", mask)
	}
	rows := b.Rows()
	if rows[Vis-1] != "#########." || rows[Vis-2] != "#########." {
		t.Errorf("끌어내린 결과가 틀렸다:\n%s", strings.Join(rows[Vis-4:], "\n"))
	}
}

// 연속으로 붙은 줄 넷(테트리스)도 한 번에 지워져야 한다.
// 지운 뒤 같은 y 를 다시 보지 않으면 여기서 두 줄만 지워진다.
func TestClearFourInARow(t *testing.T) {
	var b Board
	b.Paint(rep("##########", 4))
	if n, _ := b.ClearLines(); n != 4 {
		t.Errorf("테트리스인데 %d줄만 지웠다", n)
	}
	if !b.Empty() {
		t.Error("네 줄을 다 지웠는데 판이 안 비었다")
	}
}

func TestClearNothing(t *testing.T) {
	var b Board
	b.Paint(rep("#########.", 5))
	n, mask := b.ClearLines()
	if n != 0 || mask != 0 {
		t.Errorf("지울 게 없는데 %d줄 / 마스크 %b", n, mask)
	}
}

func TestPushRowsSharesOneHole(t *testing.T) {
	var b Board
	b.PushRows(3, 4)
	for y := H - 3; y < H; y++ {
		for x := 0; x < W; x++ {
			want := uint8(Garbage)
			if x == 4 {
				want = 0
			}
			if got := b.At(x, y); got != want {
				t.Fatalf("(%d,%d) 가 %d — %d 를 기대했다", x, y, got, want)
			}
		}
	}
}

// 밀어 올리면 위쪽이 천장 밖으로 사라진다. 배열이 곧 필드 전체라 그게 정상이다.
func TestPushRowsShiftsExistingUp(t *testing.T) {
	var b Board
	b.Paint([]string{"##########"})
	b.PushRows(1, 0)
	if b.At(1, H-2) == 0 {
		t.Error("기존 줄이 한 칸 위로 안 올라갔다")
	}
	if b.At(1, H-1) != Garbage {
		t.Error("바닥이 가비지가 아니다")
	}
}

func TestPushRowsIsCappedAtBoardHeight(t *testing.T) {
	var b Board
	b.PushRows(H+10, 0) // 판보다 많이 밀어도 죽지 않아야 한다
	if b.At(1, 0) != Garbage {
		t.Error("맨 윗줄이 가비지가 아니다")
	}
	if b.At(0, 0) != 0 {
		t.Error("맨 윗줄에도 구멍이 있어야 한다")
	}
}

func TestPushRowsZeroIsNoop(t *testing.T) {
	var b Board
	b.PushRows(0, 3)
	if !b.Empty() {
		t.Error("0줄을 밀었는데 판이 바뀌었다")
	}
}

// 해시는 판의 내용에만 의존하고, 한 칸만 달라도 값이 달라져야 한다.
func TestBoardHashChangesWithContent(t *testing.T) {
	var a, b Board
	if BoardHash(&a) != BoardHash(&b) {
		t.Fatal("같은 빈 판의 해시가 다르다")
	}
	b.Set(3, 5, 1)
	if BoardHash(&a) == BoardHash(&b) {
		t.Error("한 칸을 칠했는데 해시가 같다")
	}
}

// FNV-1a 의 시작값과 곱수가 JS 쪽 도구와 같아야 골든 트레이스를 대조할 수 있다.
// 빈 판(240바이트의 0)의 해시를 직접 계산해 못 박아 둔다.
func TestBoardHashMatchesFnv1a(t *testing.T) {
	var b Board
	h := uint32(2166136261)
	for i := 0; i < H*W; i++ {
		h ^= 0
		h *= 16777619
	}
	if got := BoardHash(&b); got != h {
		t.Errorf("빈 판의 해시가 %d — FNV-1a 로는 %d 다", got, h)
	}
}
