package core

import "testing"

func TestAttackTable(t *testing.T) {
	cases := []struct {
		n, tspin, want int
	}{
		{0, TSpinNone, 0},
		{1, TSpinNone, 0}, // 싱글은 공격이 안 된다 — 이 표의 핵심
		{2, TSpinNone, 1},
		{3, TSpinNone, 2},
		{4, TSpinNone, 4},
		{1, TSpinFull, 2},
		{2, TSpinFull, 4},
		{3, TSpinFull, 6},
		{1, TSpinMini, 0},
		{2, TSpinMini, 1},
	}
	for _, c := range cases {
		if got := Attack(c.n, c.tspin, false, -1, false); got != c.want {
			t.Errorf("%d줄 tspin=%d → %d줄 공격 — %d 를 기대했다", c.n, c.tspin, got, c.want)
		}
	}
}

// 줄을 못 지우면 공격은 0 이다. 콤보나 B2B 가 남아 있어도 마찬가지다.
func TestNoLinesNoAttack(t *testing.T) {
	if got := Attack(0, TSpinFull, true, 9, true); got != 0 {
		t.Errorf("0줄인데 %d줄 공격이 나왔다", got)
	}
}

// B2B 는 "어려운 클리어"에만 +1 이다. 싱글·더블·트리플에는 안 붙는다.
func TestBackToBackBonusOnlyForDifficult(t *testing.T) {
	if got := Attack(4, TSpinNone, true, -1, false); got != 5 {
		t.Errorf("B2B 테트리스가 %d줄 — 5줄을 기대했다", got)
	}
	if got := Attack(2, TSpinNone, true, -1, false); got != 1 {
		t.Errorf("B2B 상태의 더블이 %d줄 — 1줄이어야 한다", got)
	}
	if got := Attack(1, TSpinFull, true, -1, false); got != 3 {
		t.Errorf("B2B T스핀 싱글이 %d줄 — 3줄을 기대했다", got)
	}
}

func TestComboBonus(t *testing.T) {
	// 콤보 0(첫 클리어)에는 보너스가 없다.
	if got := Attack(2, TSpinNone, false, 0, false); got != 1 {
		t.Errorf("콤보 0 의 더블이 %d줄", got)
	}
	// 콤보 2 → 표에서 +1
	if got := Attack(2, TSpinNone, false, 2, false); got != 2 {
		t.Errorf("콤보 2 의 더블이 %d줄 — 2줄을 기대했다", got)
	}
	// 콤보 12 → 표의 천장 +5
	if got := Attack(2, TSpinNone, false, 12, false); got != 6 {
		t.Errorf("콤보 12 의 더블이 %d줄 — 6줄을 기대했다", got)
	}
}

// 콤보 값은 -1(콤보 없음)부터 들어오고 위로는 끝이 없다. 표를 벗어나면 안 된다.
func TestComboIsClampedToTheTable(t *testing.T) {
	base := Attack(2, TSpinNone, false, 12, false)
	for _, c := range []int{13, 50, 1000} {
		if got := Attack(2, TSpinNone, false, c, false); got != base {
			t.Errorf("콤보 %d 가 %d줄 — 천장인 %d줄이어야 한다", c, got, base)
		}
	}
	if got := Attack(2, TSpinNone, false, -5, false); got != 1 {
		t.Errorf("콤보 -5 가 %d줄 — 콤보 없음과 같아야 한다", got)
	}
}

func TestPerfectClearBonus(t *testing.T) {
	if got := Attack(4, TSpinNone, false, -1, true); got != 14 {
		t.Errorf("퍼펙트 테트리스가 %d줄 — 4+10 = 14줄이어야 한다", got)
	}
}

func TestComboAttackTableShape(t *testing.T) {
	if len(ComboAttack) != 13 {
		t.Fatalf("콤보표가 %d칸이다", len(ComboAttack))
	}
	for i := 1; i < len(ComboAttack); i++ {
		if ComboAttack[i] < ComboAttack[i-1] {
			t.Errorf("콤보 %d 에서 보너스가 줄었다: %d → %d", i, ComboAttack[i-1], ComboAttack[i])
		}
	}
}
