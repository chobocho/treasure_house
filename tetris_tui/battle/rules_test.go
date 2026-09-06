package battle

import (
	"testing"

	"treasure/tetris_tui/core"
)

func rep(row string, n int) []string {
	out := make([]string, n)
	for i := range out {
		out[i] = row
	}
	return out
}

func TestSeatOther(t *testing.T) {
	if Left.Other() != Right || Right.Other() != Left {
		t.Errorf("상대 자리가 틀렸다: %d, %d", Left.Other(), Right.Other())
	}
}

// 난이도는 2편의 표를 그대로 옮긴 것이다. 값이 바뀌면 "같은 AI"가 아니게 된다.
func TestLevelPresets(t *testing.T) {
	want := map[string]struct{ think, move, blunder int }{
		"easy":   {520, 110, 22},
		"normal": {380, 80, 10},
		"hard":   {260, 55, 3},
		"max":    {150, 32, 0},
	}
	lv := Levels()
	if len(lv) != len(want) {
		t.Fatalf("난이도가 %d개다", len(lv))
	}
	for _, l := range lv {
		w, ok := want[l.Name]
		if !ok {
			t.Errorf("모르는 난이도 %q", l.Name)
			continue
		}
		if l.ThinkMs != w.think || l.MoveMs != w.move || l.Blunder != w.blunder {
			t.Errorf("%s: 생각 %d 손 %d 실수 %d — %d/%d/%d 를 기대했다",
				l.Name, l.ThinkMs, l.MoveMs, l.Blunder, w.think, w.move, w.blunder)
		}
		var zero [8]float32
		if [8]float32(l.Weights) == zero {
			t.Errorf("%s 의 가중치가 비었다", l.Name)
		}
	}
}

// 난이도는 쉬운 것부터 어려운 순서로 나온다. 메뉴가 이 순서를 그대로 쓴다.
func TestLevelsAreOrderedEasyToHard(t *testing.T) {
	lv := Levels()
	for i := 1; i < len(lv); i++ {
		if lv[i].ThinkMs > lv[i-1].ThinkMs {
			t.Errorf("%s(%dms) 다음에 %s(%dms) — 생각 시간이 늘었다",
				lv[i-1].Name, lv[i-1].ThinkMs, lv[i].Name, lv[i].ThinkMs)
		}
		if lv[i].Blunder > lv[i-1].Blunder {
			t.Errorf("%s 다음 %s 에서 실수 확률이 늘었다", lv[i-1].Name, lv[i].Name)
		}
	}
}

func TestLevelByName(t *testing.T) {
	if l, ok := LevelByName("hard"); !ok || l.Name != "hard" {
		t.Errorf("hard 를 못 찾았다: %+v %v", l, ok)
	}
	if _, ok := LevelByName("없음"); ok {
		t.Error("없는 난이도가 찾아졌다")
	}
}

// 두 판은 같은 시드로 시작한다. 조각 순서가 같아야 대전이 공평하다.
func TestBothSeatsGetTheSamePieces(t *testing.T) {
	m := NewMatch(7, 3)
	l := m.Game(Left).Next(5)
	r := m.Game(Right).Next(5)
	for i := range l {
		if l[i] != r[i] {
			t.Fatalf("조각 순서가 다르다: %v vs %v", l, r)
		}
	}
	if m.Game(Left) == m.Game(Right) {
		t.Fatal("두 자리가 같은 판을 가리킨다")
	}
}

// 심판이 하는 일은 숫자 하나를 옮기는 것뿐이다.
// 왼쪽이 테트리스를 내면 오른쪽의 대기줄이 4 늘어야 한다.
func TestAttackIsDeliveredToTheOpponent(t *testing.T) {
	m := NewMatch(1, 3)
	g := m.Game(Left)
	g.Paint(append(rep(".#########", 4), "#########."))
	g.SetPiece(core.PieceI)
	g.Press(core.ActCW)
	for i := 0; i < 6; i++ {
		g.Press(core.ActLeft)
	}
	g.Press(core.ActHard)
	if got := g.Stats().Attack; got != 4 {
		t.Fatalf("테트리스인데 공격이 %d 다", got)
	}
	m.Transfer()
	if got := m.Game(Right).Stats().Pending; got != 4 {
		t.Errorf("상대의 대기줄이 %d — 4 여야 한다", got)
	}
	if got := m.Sent(Left); got != 4 {
		t.Errorf("보낸 줄 누계가 %d 다", got)
	}
}

// 같은 락을 두 번 배달하면 안 된다. 심판은 락 이벤트 번호로 새 락을 알아본다.
func TestTheSameLockIsDeliveredOnlyOnce(t *testing.T) {
	m := NewMatch(1, 3)
	g := m.Game(Left)
	g.Paint(append(rep(".#########", 4), "#########."))
	g.SetPiece(core.PieceI)
	g.Press(core.ActCW)
	for i := 0; i < 6; i++ {
		g.Press(core.ActLeft)
	}
	g.Press(core.ActHard)
	m.Transfer()
	m.Transfer()
	m.Transfer()
	if got := m.Game(Right).Stats().Pending; got != 4 {
		t.Errorf("대기줄이 %d — 같은 락이 여러 번 배달됐다", got)
	}
}

// 줄을 못 지운 락은 공격이 0 이다. 그래도 이벤트는 소비돼야 한다.
func TestNonScoringLockSendsNothing(t *testing.T) {
	m := NewMatch(1, 3)
	m.Game(Left).Press(core.ActHard)
	m.Transfer()
	if got := m.Game(Right).Stats().Pending; got != 0 {
		t.Errorf("대기줄이 %d 다", got)
	}
}

// Advance 는 두 판을 함께 굴리고 배달까지 한다.
func TestAdvanceRunsBothSeats(t *testing.T) {
	m := NewMatch(1, 3)
	m.Advance(50)
	for _, s := range []Seat{Left, Right} {
		if got := m.Game(s).Stats().Elapsed; got != 50 {
			t.Errorf("%d번 자리의 경과 시간이 %d 다", s, got)
		}
	}
}

// 한쪽이 죽으면 라운드가 끝나고 상대가 이긴다.
func TestKnockOut(t *testing.T) {
	m := NewMatch(1, 3)
	if _, _, over := m.RoundOver(); over {
		t.Fatal("시작하자마자 라운드가 끝났다")
	}
	m.Game(Left).Paint(rep("##########", core.H))
	m.Game(Left).SetPiece(core.PieceO)
	m.Advance(1)

	w, draw, over := m.RoundOver()
	if !over {
		t.Fatal("한쪽이 죽었는데 라운드가 안 끝났다")
	}
	if draw {
		t.Error("무승부로 잡혔다")
	}
	if w != Right {
		t.Errorf("승자가 %d 다 — 오른쪽이어야 한다", w)
	}
	if m.Wins(Right) != 1 {
		t.Errorf("오른쪽의 승수가 %d 다", m.Wins(Right))
	}
}

// 둘이 동시에 죽으면 무승부다. 아무도 승수를 얻지 않는다.
func TestSimultaneousDeathIsADraw(t *testing.T) {
	m := NewMatch(1, 3)
	for _, s := range []Seat{Left, Right} {
		m.Game(s).Paint(rep("##########", core.H))
		m.Game(s).SetPiece(core.PieceO)
	}
	m.Advance(1)
	_, draw, over := m.RoundOver()
	if !over || !draw {
		t.Errorf("무승부가 아니다: over=%v draw=%v", over, draw)
	}
	if m.Wins(Left) != 0 || m.Wins(Right) != 0 {
		t.Errorf("무승부인데 승수가 %d:%d 다", m.Wins(Left), m.Wins(Right))
	}
}

// 라운드가 끝난 뒤에는 시간이 흘러도 판이 안 움직인다.
func TestRoundOverFreezesTheMatch(t *testing.T) {
	m := NewMatch(1, 3)
	m.Game(Left).Paint(rep("##########", core.H))
	m.Game(Left).SetPiece(core.PieceO)
	m.Advance(1)
	el := m.Game(Right).Stats().Elapsed
	m.Advance(100)
	if got := m.Game(Right).Stats().Elapsed; got != el {
		t.Errorf("라운드가 끝났는데 시간이 %d → %d 로 흘렀다", el, got)
	}
}

// 다음 라운드는 새 판으로 시작하되 승수는 그대로 이어진다.
func TestNextRound(t *testing.T) {
	m := NewMatch(1, 3)
	m.Game(Left).Paint(rep("##########", core.H))
	m.Game(Left).SetPiece(core.PieceO)
	m.Advance(1)
	if m.Round() != 1 {
		t.Fatalf("라운드가 %d 다", m.Round())
	}
	m.NextRound()
	if m.Round() != 2 {
		t.Errorf("다음 라운드가 %d 다", m.Round())
	}
	if m.Wins(Right) != 1 {
		t.Error("승수가 초기화됐다")
	}
	if !m.Game(Left).Board().Empty() {
		t.Error("새 라운드인데 판이 안 비었다")
	}
	if _, _, over := m.RoundOver(); over {
		t.Error("새 라운드가 끝난 상태로 시작했다")
	}
}

// 라운드마다 조각 순서가 달라야 한다. 같으면 두 번째 판이 첫 판의 복사가 된다.
func TestNextRoundChangesThePieces(t *testing.T) {
	m := NewMatch(1, 3)
	first := m.Game(Left).Next(5)
	m.Game(Left).Paint(rep("##########", core.H))
	m.Game(Left).SetPiece(core.PieceO)
	m.Advance(1)
	m.NextRound()
	second := m.Game(Left).Next(5)
	same := true
	for i := range first {
		if first[i] != second[i] {
			same = false
			break
		}
	}
	if same {
		t.Error("라운드가 바뀌었는데 조각 순서가 같다")
	}
	// 그래도 두 자리는 서로 같아야 한다
	r := m.Game(Right).Next(5)
	for i := range second {
		if second[i] != r[i] {
			t.Fatalf("새 라운드에서 두 자리의 조각이 다르다: %v vs %v", second, r)
		}
	}
}

// 3판 2선승. 두 번 이기면 대전이 끝난다.
func TestBestOfThree(t *testing.T) {
	m := NewMatch(1, 3)
	killLeft := func() {
		m.Game(Left).Paint(rep("##########", core.H))
		m.Game(Left).SetPiece(core.PieceO)
		m.Advance(1)
	}
	killLeft()
	if _, done := m.MatchOver(); done {
		t.Fatal("한 판 만에 대전이 끝났다")
	}
	m.NextRound()
	killLeft()
	w, done := m.MatchOver()
	if !done {
		t.Fatal("2승인데 대전이 안 끝났다")
	}
	if w != Right {
		t.Errorf("대전 승자가 %d 다", w)
	}
	// 끝난 뒤 NextRound 는 아무 일도 하지 않아야 한다
	round := m.Round()
	m.NextRound()
	if m.Round() != round {
		t.Error("대전이 끝났는데 다음 라운드가 시작됐다")
	}
}

func TestRestart(t *testing.T) {
	m := NewMatch(1, 3)
	m.Game(Left).Paint(rep("##########", core.H))
	m.Game(Left).SetPiece(core.PieceO)
	m.Advance(1)
	m.Restart()
	if m.Wins(Left) != 0 || m.Wins(Right) != 0 || m.Round() != 1 {
		t.Errorf("다시 시작이 덜 됐다: %d:%d 라운드 %d", m.Wins(Left), m.Wins(Right), m.Round())
	}
	if _, done := m.MatchOver(); done {
		t.Error("다시 시작했는데 끝난 상태다")
	}
	if m.Sent(Left) != 0 {
		t.Errorf("보낸 줄 누계가 %d 다", m.Sent(Left))
	}
}
