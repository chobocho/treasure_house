package core

import "testing"

// 판 크기는 여러 곳에서 인덱스 계산에 쓰인다. 하나라도 어긋나면
// 골든 트레이스가 통째로 갈라지므로 값 자체를 못 박아 둔다.
func TestDimensions(t *testing.T) {
	if W != 10 || Vis != 20 || Hidden != 4 || H != 24 {
		t.Fatalf("판 크기가 %d×%d(숨은 %d, 전체 %d) 다", W, Vis, Hidden, H)
	}
	if SpawnY != Hidden {
		t.Errorf("스폰 y 가 %d 다 — 보이는 판의 맨 윗줄이어야 한다", SpawnY)
	}
}

// 모든 조각은 어느 회전 상태에서든 정확히 네 칸이다. 표를 손으로 옮겼으므로
// 오타 한 글자가 조각을 세 칸짜리로 만들 수 있다 — 그걸 잡는 테스트다.
func TestEveryShapeHasFourCells(t *testing.T) {
	for p := 0; p < PieceCount; p++ {
		for r := 0; r < 4; r++ {
			n := 0
			for i := 0; i < 16; i++ {
				if Shapes[p][r]&(1<<uint(i)) != 0 {
					n++
				}
			}
			if n != 4 {
				t.Errorf("%s 조각 rot%d 이 %d칸이다", PieceNames[p], r, n)
			}
		}
	}
}

// O 조각만 회전해도 모양이 같다. 나머지는 rot0 과 rot1 이 반드시 다르다.
func TestOnlyOIsRotationInvariant(t *testing.T) {
	for p := 0; p < PieceCount; p++ {
		same := Shapes[p][0] == Shapes[p][1]
		if (p == PieceO) != same {
			t.Errorf("%s: rot0==rot1 이 %v 다", PieceNames[p], same)
		}
	}
}

// I 와 S/Z 는 두 번 돌리면 제자리로 온다(2중 대칭). 표가 그 성질을 지키는지 본다.
func TestTwoFoldSymmetry(t *testing.T) {
	for _, p := range []int{PieceI, PieceS, PieceZ} {
		// 모양 자체는 위치가 달라 같지 않을 수 있으므로 칸 수만 보지 않고
		// "네 상태 중 서로 다른 모양이 몇 가지인가"로 확인한다.
		set := map[uint16]bool{}
		for r := 0; r < 4; r++ {
			set[Shapes[p][r]] = true
		}
		if len(set) != 4 {
			t.Errorf("%s 의 서로 다른 모양이 %d가지다 — 표에 중복이 있다", PieceNames[p], len(set))
		}
	}
}

func TestBlocksMatchesTheBitmask(t *testing.T) {
	for p := 0; p < PieceCount; p++ {
		for r := 0; r < 4; r++ {
			got := Blocks(p, r)
			var m uint16
			for _, b := range got {
				if b[0] < 0 || b[0] > 3 || b[1] < 0 || b[1] > 3 {
					t.Fatalf("%s rot%d: 범위 밖 칸 %v", PieceNames[p], r, b)
				}
				m |= 1 << uint(b[1]*4+b[0])
			}
			if m != Shapes[p][r] {
				t.Errorf("%s rot%d: Blocks 가 0x%04X 를 되살렸다 — 0x%04X 여야 한다",
					PieceNames[p], r, m, Shapes[p][r])
			}
		}
	}
}

// 회전 인덱스는 4로 나눈 나머지를 쓴다. 4나 -1 이 들어와도 죽지 않아야
// 회전 계산에서 매번 & 3 을 쓰는 것을 잊어도 안전하다.
func TestRotationIndexWrapsAround(t *testing.T) {
	if Blocks(PieceT, 4) != Blocks(PieceT, 0) {
		t.Error("rot 4 가 rot 0 과 다르다")
	}
	if ShapeBottom(PieceT, 4) != ShapeBottom(PieceT, 0) {
		t.Error("ShapeBottom 의 rot 4 가 rot 0 과 다르다")
	}
}

func TestShapeBottom(t *testing.T) {
	cases := []struct {
		piece, rot, want int
	}{
		{PieceI, 0, 1}, // 0x00F0 → y=1 줄에 가로 막대
		{PieceI, 1, 3}, // 0x2222 → y=0..3 세로 막대
		{PieceO, 0, 1}, // 0x0066 → y=0,1
		{PieceT, 0, 1}, // 0x0072 → y=0,1
	}
	for _, c := range cases {
		if got := ShapeBottom(c.piece, c.rot); got != c.want {
			t.Errorf("%s rot%d 의 맨 아랫줄이 %d — %d 를 기대했다",
				PieceNames[c.piece], c.rot, got, c.want)
		}
	}
}
