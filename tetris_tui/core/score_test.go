package core

import "testing"

// 중력표는 가이드라인 공식을 미리 계산해 굳힌 것이다.
// 단조 감소여야 하고(레벨이 오를수록 빨라진다) 0 이 되면 안 된다(무한 루프).
func TestGravityTableIsMonotonicAndPositive(t *testing.T) {
	for lv := 1; lv < MaxLevel; lv++ {
		if GravityMs[lv+1] > GravityMs[lv] {
			t.Errorf("레벨 %d(%dms) → %d(%dms) 에서 느려졌다",
				lv, GravityMs[lv], lv+1, GravityMs[lv+1])
		}
	}
	for lv := 1; lv <= MaxLevel; lv++ {
		if GravityMs[lv] == 0 {
			t.Errorf("레벨 %d 의 낙하 간격이 0 이다", lv)
		}
	}
}

func TestGravityKnownValues(t *testing.T) {
	cases := [][2]int{{1, 1000}, {5, 355}, {10, 64}, {20, 1}}
	for _, c := range cases {
		if got := Gravity(c[0]); got != c[1] {
			t.Errorf("레벨 %d 의 낙하 간격이 %d — %d 를 기대했다", c[0], got, c[1])
		}
	}
}

// 범위 밖 레벨은 양 끝으로 자른다. 0 이나 21 이 들어와도 인덱스가 튀면 안 된다.
func TestGravityClampsOutOfRange(t *testing.T) {
	if Gravity(0) != Gravity(1) {
		t.Error("레벨 0 이 레벨 1 로 안 잘렸다")
	}
	if Gravity(999) != Gravity(MaxLevel) {
		t.Error("레벨 999 가 최대 레벨로 안 잘렸다")
	}
}

func TestLineScoreTable(t *testing.T) {
	cases := []struct {
		n, tspin, base int
		difficult      bool
	}{
		{0, TSpinNone, 0, false},
		{1, TSpinNone, 100, false},
		{2, TSpinNone, 300, false},
		{3, TSpinNone, 500, false},
		{4, TSpinNone, 800, true}, // 테트리스는 어려운 클리어
		{0, TSpinFull, 400, false},
		{1, TSpinFull, 800, true},
		{2, TSpinFull, 1200, true},
		{3, TSpinFull, 1600, true},
		{0, TSpinMini, 100, false},
		{1, TSpinMini, 200, true},
		{2, TSpinMini, 400, true},
	}
	for _, c := range cases {
		base, hard := LineScore(c.n, c.tspin)
		if base != c.base || hard != c.difficult {
			t.Errorf("%d줄 tspin=%d → (%d, %v) — (%d, %v) 를 기대했다",
				c.n, c.tspin, base, hard, c.base, c.difficult)
		}
	}
}

// 줄을 못 지운 T스핀(0줄)은 점수는 주지만 "어려운 클리어"가 아니다 —
// B2B 는 클리어가 있어야 이어진다. 이 구분을 놓치면 B2B 가 영원히 안 끊긴다.
func TestZeroLineSpinIsNotDifficult(t *testing.T) {
	if _, hard := LineScore(0, TSpinFull); hard {
		t.Error("0줄 T스핀이 어려운 클리어로 잡혔다")
	}
	if _, hard := LineScore(0, TSpinMini); hard {
		t.Error("0줄 미니 T스핀이 어려운 클리어로 잡혔다")
	}
}

func TestLevelFor(t *testing.T) {
	cases := [][2]int{{0, 1}, {9, 1}, {10, 2}, {19, 2}, {20, 3}, {190, 20}, {500, 20}}
	for _, c := range cases {
		if got := LevelFor(c[0]); got != c[1] {
			t.Errorf("%d줄에서 레벨 %d — %d 를 기대했다", c[0], got, c[1])
		}
	}
}
