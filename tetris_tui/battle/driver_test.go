package battle

import (
	"testing"

	"treasure/tetris_tui/ai"
	"treasure/tetris_tui/core"
)

func hardLevel(t *testing.T) Level {
	t.Helper()
	l, ok := LevelByName("hard")
	if !ok {
		t.Fatal("hard 난이도가 없다")
	}
	return l
}

// 드라이버는 생각 시간이 지나야 탐색을 요청한다.
// 즉시 두면 조각이 순간이동한 것처럼 보이고, 사람은 무슨 일이 일어났는지 못 본다.
func TestDriverWaitsBeforeAskingForAPlan(t *testing.T) {
	lv := hardLevel(t)
	d := NewDriver(lv, 1)
	g := core.New(1)

	elapsed := 0
	for elapsed+16 < lv.ThinkMs {
		if s := d.Tick(g, 16); s.Kind != StepNone {
			t.Fatalf("%dms 만에 %d 를 요구했다 — 생각 시간은 %dms 다", elapsed, s.Kind, lv.ThinkMs)
		}
		elapsed += 16
	}
	for i := 0; i < 3; i++ {
		if s := d.Tick(g, 16); s.Kind == StepPlan {
			return
		}
	}
	t.Errorf("생각 시간이 지났는데 탐색을 요청하지 않았다")
}

// 탐색을 요청한 뒤에는 결과가 올 때까지 다시 요청하지 않는다.
// 겹쳐 띄우면 Cmd 가 여러 개 돌고 결과가 두 번 와서 조각이 두 번 움직인다.
func TestDriverDoesNotAskTwice(t *testing.T) {
	lv := hardLevel(t)
	d := NewDriver(lv, 1)
	g := core.New(1)
	askUntilPlan(t, d, g)
	for i := 0; i < 40; i++ {
		if s := d.Tick(g, 16); s.Kind == StepPlan {
			t.Fatal("결과를 기다리는 중에 또 탐색을 요청했다")
		}
	}
	if !d.Thinking() {
		t.Error("생각 중 표시가 꺼져 있다")
	}
}

func askUntilPlan(t *testing.T, d *Driver, g *core.Game) {
	t.Helper()
	for i := 0; i < 200; i++ {
		if d.Tick(g, 16).Kind == StepPlan {
			return
		}
	}
	t.Fatal("탐색 요청이 오지 않았다")
}

// 목표를 받으면 손 속도(MoveMs)마다 키를 하나씩 누른다.
func TestDriverPressesOneKeyPerMoveInterval(t *testing.T) {
	lv := hardLevel(t)
	d := NewDriver(lv, 1)
	g := core.New(1)
	askUntilPlan(t, d, g)
	d.SetTarget(ai.Move{Rot: 1, X: 0}, true)

	presses := 0
	for i := 0; i < lv.MoveMs/16+2; i++ {
		if d.Tick(g, 16).Kind == StepPress {
			presses++
		}
	}
	if presses != 1 {
		t.Errorf("%dms 동안 키를 %d번 눌렀다 — 손 속도는 %dms 다", lv.MoveMs+32, presses, lv.MoveMs)
	}
}

// 드라이버는 목표에 도달할 때까지 **매번 지금 상태를 보고** 다음 키를 정한다.
// 미리 키 목록을 만들어 두면 회전 킥이 x 를 밀었을 때 어긋난다.
func TestDriverSteersTowardTheTarget(t *testing.T) {
	lv := hardLevel(t)
	d := NewDriver(lv, 1)
	g := core.New(1)
	g.SetPiece(core.PieceT)
	askUntilPlan(t, d, g)
	target := ai.Move{Rot: 2, X: 0}
	d.SetTarget(target, true)

	locked := g.Stats().Pieces
	for i := 0; i < 400; i++ {
		s := d.Tick(g, 16)
		if s.Kind != StepPress {
			continue
		}
		g.Press(s.Act)
		if s.Act == core.ActLeft || s.Act == core.ActRight {
			g.Release(s.Act)
		}
		if g.Stats().Pieces != locked {
			break // 굳었다 = 하드드롭까지 갔다
		}
	}
	if g.Stats().Pieces == locked {
		t.Fatal("조각을 못 굳혔다")
	}
	// 굳기 직전의 자리를 다시 볼 수는 없으므로, 판에 T 색(6)이 남았는지로 확인한다.
	found := false
	for y := 0; y < core.H; y++ {
		for x := 0; x < 4; x++ {
			if g.Board().At(x, y) == core.PieceT+1 {
				found = true
			}
		}
	}
	if !found {
		t.Errorf("목표 x=%d 근처에 조각이 없다:\n%v", target.X, g.Board().Rows()[core.Vis-4:])
	}
}

// 회전이 막혀서 목표에 영영 못 가는 경우가 있다. 그때는 그냥 떨어뜨린다 —
// 안 그러면 드라이버가 같은 키를 무한히 누르며 판이 멈춘다.
func TestDriverGivesUpAndDrops(t *testing.T) {
	lv := hardLevel(t)
	d := NewDriver(lv, 1)
	g := core.New(1)
	askUntilPlan(t, d, g)
	// 도달할 수 없는 목표 — O 조각은 회전해도 rot 이 안 바뀐다.
	g.SetPiece(core.PieceO)
	d.SetTarget(ai.Move{Rot: 3, X: 0}, true)

	sawHard := false
	for i := 0; i < 2000; i++ {
		s := d.Tick(g, 16)
		if s.Kind != StepPress {
			continue
		}
		if s.Act == core.ActHard {
			sawHard = true
			break
		}
		g.Press(s.Act)
	}
	if !sawHard {
		t.Error("도달 불가능한 목표인데 포기하고 떨어뜨리지 않았다")
	}
}

// 실수 확률이 100%면 매번 엉뚱한 자리를 고른다. 난이도를 낮추는 정직한 방법 —
// 규칙을 봐주는 게 아니라 "가끔 잘못 둔다"로 약하게 만든다.
func TestBlunderReplacesTheTarget(t *testing.T) {
	lv := hardLevel(t)
	lv.Blunder = 100
	d := NewDriver(lv, 12345)
	g := core.New(1)

	want := ai.Move{UseHold: true, Rot: 1, X: 5}
	changed := 0
	for i := 0; i < 20; i++ {
		d.Reset()
		askUntilPlan(t, d, g)
		d.SetTarget(want, true)
		if got := d.Target(); got != want {
			changed++
		}
	}
	if changed != 20 {
		t.Errorf("실수 확률 100%%인데 %d/20 만 바뀌었다", changed)
	}
}

func TestNoBlunderKeepsTheTarget(t *testing.T) {
	lv := hardLevel(t)
	lv.Blunder = 0
	d := NewDriver(lv, 1)
	g := core.New(1)
	askUntilPlan(t, d, g)
	want := ai.Move{UseHold: true, Rot: 2, X: 7}
	d.SetTarget(want, true)
	if got := d.Target(); got != want {
		t.Errorf("실수 확률 0 인데 목표가 %+v 로 바뀌었다", got)
	}
}

// 실수는 시드가 있는 난수로 정한다. 브라우저 판은 Math.random 을 썼지만,
// 여기서는 기록을 다시 돌렸을 때 같은 결과가 나와야 한다.
func TestBlunderIsDeterministic(t *testing.T) {
	lv := hardLevel(t)
	lv.Blunder = 50
	run := func() []ai.Move {
		d := NewDriver(lv, 99)
		g := core.New(1)
		var out []ai.Move
		for i := 0; i < 10; i++ {
			d.Reset()
			askUntilPlan(t, d, g)
			d.SetTarget(ai.Move{Rot: 1, X: 4}, true)
			out = append(out, d.Target())
		}
		return out
	}
	a, b := run(), run()
	for i := range a {
		if a[i] != b[i] {
			t.Fatalf("같은 시드인데 %d번째 결과가 다르다: %+v vs %+v", i, a[i], b[i])
		}
	}
}

// 탐색이 "둘 수 없음"을 돌려주면 목표를 세우지 않는다.
func TestSetTargetWithNoMove(t *testing.T) {
	d := NewDriver(hardLevel(t), 1)
	g := core.New(1)
	askUntilPlan(t, d, g)
	d.SetTarget(ai.Move{}, false)
	if d.Thinking() {
		t.Error("결과를 받았는데 생각 중 표시가 남아 있다")
	}
	for i := 0; i < 20; i++ {
		if d.Tick(g, 16).Kind == StepPress {
			t.Fatal("목표가 없는데 키를 눌렀다")
		}
	}
}

// 게임 오버 뒤에는 아무것도 안 한다.
func TestDriverStopsWhenTheGameIsOver(t *testing.T) {
	d := NewDriver(hardLevel(t), 1)
	g := core.New(1)
	g.Paint(rep("##########", core.H))
	g.SetPiece(core.PieceO)
	for i := 0; i < 200; i++ {
		if s := d.Tick(g, 16); s.Kind != StepNone {
			t.Fatalf("게임 오버인데 %d 를 요구했다", s.Kind)
		}
	}
}

func TestResetClearsEverything(t *testing.T) {
	d := NewDriver(hardLevel(t), 1)
	g := core.New(1)
	askUntilPlan(t, d, g)
	d.SetTarget(ai.Move{Rot: 1, X: 2}, true)
	d.Reset()
	if d.Thinking() {
		t.Error("Reset 뒤에도 생각 중이다")
	}
	if s := d.Tick(g, 16); s.Kind == StepPress {
		t.Error("Reset 뒤에도 목표가 남아 있다")
	}
}
