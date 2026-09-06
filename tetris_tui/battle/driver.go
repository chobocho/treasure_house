package battle

import (
	"treasure/tetris_tui/ai"
	"treasure/tetris_tui/core"
)

// driver.go — AI 의 "손".
//
// ai.Best 는 1밀리초도 안 걸려 답을 낸다. 그 답을 즉시 판에 꽂으면 사람 눈에는
// 조각이 순간이동한 것으로 보이고, 무슨 일이 일어났는지 배울 수가 없다.
// 그래서 계획을 목표(rot, x)로 들고 있다가 MoveMs 마다 키를 하나씩만 누른다.
// 조작 경로가 사람과 완전히 같아진다 — AI 는 규칙을 우회하지 않는다.
//
// 이 파일에는 탐색이 없다. 탐색은 Update 바깥의 Cmd 에서 돈다(model.go 참고).
// 드라이버는 "지금 탐색을 시작해 달라"고 요청하고, 결과를 SetTarget 으로 받는다.

// StepKind 는 드라이버가 이번 틱에 요구하는 일.
type StepKind int

const (
	StepNone  StepKind = iota
	StepPlan           // 지금 탐색을 시작해 달라 (모델이 Cmd 를 띄운다)
	StepPress          // 지금 이 키를 눌러 달라
)

// Step 은 드라이버가 이번 틱에 내는 지시.
type Step struct {
	Kind StepKind
	Act  core.Action
}

// guardMax 는 한 조각에 눌러 볼 수 있는 키의 최대 개수.
//
// 목표에 못 가는 경우가 있다 — 회전이 막혔거나, 실수(blunder)로 도달 불가능한
// 자리를 골랐거나. 상한이 없으면 드라이버가 같은 키를 무한히 누르며 판이 멈춘다.
// 24 는 "회전 3 + 좌우 최대 12 + 여유"에서 나온 값이다.
const guardMax = 24

// Driver 는 AI 한 자리의 손이다.
type Driver struct {
	level  Level
	rng    *core.Rng
	target ai.Move
	have   bool
	busy   bool // 탐색 결과를 기다리는 중
	t      int  // 마지막 사건 이후 흐른 ms
	guard  int
}

// NewDriver 는 난이도와 시드로 드라이버를 만든다.
//
// 시드가 있는 난수를 쓰는 이유: 실수(blunder)를 math/rand 로 뽑으면 기록을
// 다시 돌렸을 때 다른 판이 나온다. 브라우저 판(2편)은 Math.random 을 썼지만,
// 여기서는 out/frames_*.json 이 바이트까지 재현돼야 한다.
func NewDriver(lv Level, seed uint32) *Driver {
	return &Driver{level: lv, rng: core.NewRng(seed)}
}

// Level 은 이 드라이버의 난이도.
func (d *Driver) Level() Level { return d.level }

// Thinking 은 지금 탐색 결과를 기다리는 중인지. 화면이 "생각 중…"을 띄우는 데 쓴다.
func (d *Driver) Thinking() bool { return d.busy }

// Target 은 지금 목표. 테스트와 화면이 들여다본다.
func (d *Driver) Target() ai.Move { return d.target }

// Tick 은 시간을 흘리고 이번에 할 일을 정한다.
//
// 상태 기계가 셋뿐이다:
//
//	목표 없음 + 안 기다림 → ThinkMs 를 채우면 StepPlan
//	목표 없음 + 기다리는 중 → 아무것도 안 함 (결과가 SetTarget 으로 온다)
//	목표 있음 → MoveMs 마다 StepPress 하나
func (d *Driver) Tick(g *core.Game, dtMs int) Step {
	if g.Stats().State != core.StatePlay {
		return Step{}
	}
	d.t += dtMs

	if !d.have {
		if d.busy {
			return Step{}
		}
		if d.t < d.level.ThinkMs {
			return Step{}
		}
		d.t = 0
		d.busy = true
		return Step{Kind: StepPlan}
	}

	if d.t < d.level.MoveMs {
		return Step{}
	}
	d.t = 0

	d.guard++
	if d.guard > guardMax {
		d.finish()
		return Step{Kind: StepPress, Act: core.ActHard}
	}
	return Step{Kind: StepPress, Act: d.nextAction(g)}
}

// nextAction 은 **지금 판을 보고** 다음 키 하나를 고른다.
//
// 왜 미리 키 목록을 만들어 두지 않는가. 회전은 킥으로 x 를 밀 수 있다.
// "CW 두 번, 왼쪽 세 번, 하드드롭" 같은 목록을 미리 만들면 킥이 일어난 순간
// 어긋나고, 조각이 엉뚱한 자리에 떨어진다. 매번 다시 보면 저절로 교정된다.
func (d *Driver) nextAction(g *core.Game) core.Action {
	s := g.Stats()
	if d.target.UseHold {
		d.target.UseHold = false
		return core.ActHold
	}
	if int(s.Rot) != d.target.Rot {
		return core.ActCW
	}
	if int(s.X) > d.target.X {
		return core.ActLeft
	}
	if int(s.X) < d.target.X {
		return core.ActRight
	}
	d.finish()
	return core.ActHard
}

// finish 는 이번 조각을 끝내고 다음 생각을 시작할 준비를 한다.
// t 를 -ThinkMs 로 두면 "다음 조각은 다시 생각 시간부터"가 된다.
func (d *Driver) finish() {
	d.have = false
	d.guard = 0
	d.t = -d.level.ThinkMs
}

// SetTarget 은 탐색이 돌려준 수를 목표로 삼는다.
//
// 실수(blunder)를 여기서 적용한다 — 탐색을 도는 Cmd 는 다른 고루틴이라
// 드라이버의 난수 상태를 건드리면 안 되기 때문이다.
func (d *Driver) SetTarget(m ai.Move, ok bool) {
	d.busy = false
	if !ok {
		d.have = false
		return
	}
	if d.level.Blunder > 0 && d.rng.IntN(100) < d.level.Blunder {
		// 회전과 위치를 아무렇게나 바꾼다. 난이도를 낮추는 가장 정직한 방법 —
		// 약한 AI 를 만들려고 규칙을 봐주는 게 아니라 "가끔 잘못 둔다"로 만든다.
		m = ai.Move{Rot: d.rng.IntN(4), X: d.rng.IntN(core.W)}
	}
	d.target = m
	d.have = true
	d.guard = 0
	d.t = 0
}

// Reset 은 라운드가 바뀔 때 드라이버를 처음 상태로 되돌린다.
func (d *Driver) Reset() {
	d.have, d.busy, d.t, d.guard = false, false, 0, 0
	d.target = ai.Move{}
}
