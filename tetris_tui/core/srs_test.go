package core

import "testing"

// 킥 표의 구조 계약. 다섯 후보이고 첫 후보는 언제나 "안 움직임"이다 —
// 막히지 않은 회전이 제자리에서 성공해야 하기 때문이다.
func TestKickTablesStartAtOrigin(t *testing.T) {
	for name, tbl := range map[string]*[4][5][2]int8{
		"JLSTZ CW": &KickJLSTZCW, "JLSTZ CCW": &KickJLSTZCCW,
		"I CW": &KickICW, "I CCW": &KickICCW,
	} {
		for from := 0; from < 4; from++ {
			if tbl[from][0] != [2]int8{0, 0} {
				t.Errorf("%s [%d] 의 첫 후보가 %v 다", name, from, tbl[from][0])
			}
		}
	}
}

// CW 로 갔다가 CCW 로 돌아오는 경로는 서로의 역이어야 한다.
// SRS 표의 정의가 그렇다: CCW(from = to) 의 후보는 CW(from) 후보의 부호 반전이다.
func TestCcwIsTheInverseOfCw(t *testing.T) {
	check := func(name string, cw, ccw *[4][5][2]int8) {
		for from := 0; from < 4; from++ {
			to := (from + 1) & 3
			for k := 0; k < 5; k++ {
				want := [2]int8{-cw[from][k][0], -cw[from][k][1]}
				if got := ccw[to][k]; got != want {
					t.Errorf("%s %d→%d 의 %d번 후보 역이 %v — %v 를 기대했다",
						name, to, from, k, got, want)
				}
			}
		}
	}
	check("JLSTZ", &KickJLSTZCW, &KickJLSTZCCW)
	check("I", &KickICW, &KickICCW)
}

func TestKickTableSelectsIForIOnly(t *testing.T) {
	if KickTable(PieceI, +1, 0) != &KickICW[0] {
		t.Error("I 조각이 전용 표를 안 쓴다")
	}
	if KickTable(PieceI, -1, 2) != &KickICCW[2] {
		t.Error("I 조각의 반시계 표가 틀렸다")
	}
	for _, p := range []int{PieceJ, PieceL, PieceO, PieceS, PieceT, PieceZ} {
		if KickTable(p, +1, 1) != &KickJLSTZCW[1] {
			t.Errorf("%s 가 I 전용 표를 쓴다", PieceNames[p])
		}
	}
}

// T스핀 코너 표의 구조. 앞뒤 각각 두 코너이고, 네 값은 전부 ±1 이다.
func TestTspinCornerTables(t *testing.T) {
	for rot := 0; rot < 4; rot++ {
		for _, tbl := range []*[4][4]int8{&tspinFront, &tspinBack} {
			for _, v := range tbl[rot] {
				if v != 1 && v != -1 {
					t.Errorf("rot%d 의 코너 오프셋에 %d 가 있다 — ±1 이어야 한다", rot, v)
				}
			}
		}
	}
}

// 앞 코너와 뒤 코너는 겹치지 않아야 한다. 겹치면 같은 코너를 두 번 세게 되어
// "앞 2개 + 뒤 1개"라는 판정이 무너진다.
func TestFrontAndBackCornersAreDisjoint(t *testing.T) {
	for rot := 0; rot < 4; rot++ {
		f := map[[2]int8]bool{
			{tspinFront[rot][0], tspinFront[rot][1]}: true,
			{tspinFront[rot][2], tspinFront[rot][3]}: true,
		}
		if len(f) != 2 {
			t.Fatalf("rot%d 의 앞 코너 둘이 같은 자리다", rot)
		}
		for _, c := range [][2]int8{
			{tspinBack[rot][0], tspinBack[rot][1]},
			{tspinBack[rot][2], tspinBack[rot][3]},
		} {
			if f[c] {
				t.Errorf("rot%d: 뒤 코너 %v 가 앞 코너와 겹친다", rot, c)
			}
		}
	}
}
