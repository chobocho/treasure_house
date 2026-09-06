// Package battle 은 1:1 대전이다 — 같은 키보드 2인용, 사람 대 AI, AI 대 AI.
//
// 셋이 한 모델을 공유한다. 다른 것은 "각 자리를 누가 조종하는가"뿐이고,
// 규칙도 화면도 완전히 같다. 그렇게 나눠야 "AI 는 사람과 다른 규칙으로 논다"는
// 의심이 원천적으로 생기지 않는다.
package battle

import (
	"treasure/tetris_tui/ai"
	"treasure/tetris_tui/core"
)

// Seat 은 대전의 한 자리.
type Seat int

const (
	Left Seat = iota
	Right
	Seats = 2
)

// Other 는 상대 자리.
func (s Seat) Other() Seat {
	if s == Left {
		return Right
	}
	return Left
}

// Level 은 AI 난이도 하나.
//
// 난이도를 "규칙을 봐주는" 방식으로 만들지 않았다. 네 가지를 조합한다:
//
//	Weights — 몇 세대까지 학습한 가중치인가 (덜 배운 AI 는 덜 잘 둔다)
//	ThinkMs — 조각 하나를 생각하는 시간 (느리면 그동안 상대가 앞서간다)
//	MoveMs  — 키 하나 사이의 간격 = 손 속도
//	Blunder — 이 확률(백분율)로 엉뚱한 자리를 고른다
//
// 숫자는 2편(C++_WASM_테트리스_AI_대전)의 표를 그대로 옮겼다.
type Level struct {
	Name    string // 깃발과 코드에서 쓰는 이름 ("hard")
	Short   string // 좁은 자리에 넣는 이름 ("어려움")
	Label   string // 사람이 읽는 전체 이름 ("어려움 (15세대)")
	ThinkMs int
	MoveMs  int
	Blunder int // 백분율. 정수로 두면 결정론적 난수와 비교하기 쉽다.
	Weights ai.Weights
}

// 난이도 표. 가중치는 실행 시점에 weights.json 에서 채운다 —
// 여기에 숫자를 다시 적으면 두 곳이 어긋날 여지가 생긴다.
var levelTable = []struct {
	name, short, label string
	think, move, bl    int
}{
	{"easy", "쉬움", "쉬움 (1세대)", 520, 110, 22},
	{"normal", "보통", "보통 (5세대)", 380, 80, 10},
	{"hard", "어려움", "어려움 (15세대)", 260, 55, 3},
	{"max", "최종", "최종 (50세대)", 150, 32, 0},
}

// Levels 는 쉬운 것부터 어려운 순서로.
func Levels() []Level {
	out := make([]Level, 0, len(levelTable))
	for _, l := range levelTable {
		w, ok := ai.Level(l.name)
		if !ok {
			continue
		}
		out = append(out, Level{
			Name: l.name, Short: l.short, Label: l.label,
			ThinkMs: l.think, MoveMs: l.move, Blunder: l.bl,
			Weights: w,
		})
	}
	return out
}

// LevelByName 은 이름으로 난이도를 찾는다.
func LevelByName(name string) (Level, bool) {
	for _, l := range Levels() {
		if l.Name == name {
			return l, true
		}
	}
	return Level{}, false
}

// Match 는 두 판과 심판이다.
//
// 심판이 하는 일은 놀랄 만큼 적다. 규칙은 전부 core 안에 있고, 심판은
// "A 의 이번 락이 n 줄을 보냈다 → B 의 대기열에 n 을 넣는다"만 한다.
// 승패 판정과 라운드 관리가 거기 붙는다.
type Match struct {
	g    [Seats]*core.Game
	seen [Seats]int32 // 마지막으로 배달한 락 이벤트 번호
	sent [Seats]int
	wins [Seats]int

	seed   uint32
	round  int
	bestOf int

	roundOver bool
	winner    Seat
	draw      bool
}

// NewMatch 는 두 판을 **같은 시드**로 시작한다.
//
// 조각 순서가 같아야 대전이 공평하다. "운이 나빠서 졌다"가 성립하면
// 실력 비교가 아니게 되고, AI 와의 대전은 특히 그 의심을 사기 쉽다.
func NewMatch(seed uint32, bestOf int) *Match {
	if bestOf < 1 {
		bestOf = 1
	}
	m := &Match{seed: seed, bestOf: bestOf, round: 1}
	for s := range m.g {
		m.g[s] = core.New(seed)
	}
	return m
}

// Game 은 한 자리의 판.
func (m *Match) Game(s Seat) *core.Game { return m.g[s] }

// Advance 는 두 판을 dtMs 만큼 진행시키고, 공격을 옮기고, 승패를 본다.
func (m *Match) Advance(dtMs int) {
	if m.roundOver {
		return
	}
	for s := range m.g {
		m.g[s].Update(dtMs)
	}
	m.Transfer()
	m.judge()
}

// Transfer 는 새로 일어난 락의 공격을 상대에게 옮긴다.
//
// "새로 일어난"을 어떻게 아는가. 코어는 락이 일어날 때마다 Event 를 1 올린다.
// 그 번호가 지난번에 본 것과 다르면 새 락이다. 이게 없으면 같은 공격을
// 매 프레임 다시 배달해서, 한 번의 테트리스가 상대를 즉사시킨다.
func (m *Match) Transfer() {
	for s := Seat(0); s < Seats; s++ {
		ev := m.g[s].Stats().Event
		if ev == m.seen[s] {
			continue
		}
		m.seen[s] = ev
		if n := int(m.g[s].Stats().Attack); n > 0 {
			m.sent[s] += n
			m.g[s.Other()].QueueGarbage(n)
		}
	}
}

// judge 는 죽은 자리가 있는지 보고 라운드를 끝낸다.
func (m *Match) judge() {
	dead := [Seats]bool{}
	n := 0
	for s := range m.g {
		if m.g[s].Stats().State == core.StateOver {
			dead[s] = true
			n++
		}
	}
	if n == 0 {
		return
	}
	m.roundOver = true
	if n == Seats {
		// 같은 프레임에 둘 다 죽었다. 아무도 이기지 않는다 —
		// 한쪽을 임의로 골라 주면 그게 곧 규칙이 되고, 아무도 그 규칙에 동의한 적이 없다.
		m.draw = true
		return
	}
	if dead[Left] {
		m.winner = Right
	} else {
		m.winner = Left
	}
	m.wins[m.winner]++
}

// Sent 는 그 자리가 지금까지 보낸 줄 수.
func (m *Match) Sent(s Seat) int { return m.sent[s] }

// Wins 는 그 자리가 딴 라운드 수.
func (m *Match) Wins(s Seat) int { return m.wins[s] }

// Round 는 지금 몇 번째 라운드인지 (1부터).
func (m *Match) Round() int { return m.round }

// BestOf 는 몇 판제인지.
func (m *Match) BestOf() int { return m.bestOf }

// RoundOver 는 이번 라운드가 끝났는지와 승자, 그리고 무승부인지.
func (m *Match) RoundOver() (winner Seat, draw bool, over bool) {
	return m.winner, m.draw, m.roundOver
}

// needed 는 대전을 끝내는 데 필요한 승수. 3판이면 2승, 5판이면 3승.
func (m *Match) needed() int { return m.bestOf/2 + 1 }

// MatchOver 는 대전 전체가 끝났는지와 승자.
func (m *Match) MatchOver() (Seat, bool) {
	for s := Seat(0); s < Seats; s++ {
		if m.wins[s] >= m.needed() {
			return s, true
		}
	}
	return 0, false
}

// NextRound 는 다음 라운드를 시작한다. 대전이 끝났으면 아무것도 안 한다.
//
// 시드를 한 칸 굴려 새 조각 순서를 만든다. 같은 시드로 다시 하면
// 2라운드가 1라운드의 복사가 되어 버린다.
func (m *Match) NextRound() {
	if _, done := m.MatchOver(); done {
		return
	}
	if !m.roundOver {
		return
	}
	m.seed = m.seed*1664525 + 1013904223
	m.round++
	m.resetRound()
}

// Restart 는 대전 전체를 처음부터 다시.
func (m *Match) Restart() {
	m.wins = [Seats]int{}
	m.round = 1
	m.seed = m.seed*1664525 + 1013904223
	m.resetRound()
}

func (m *Match) resetRound() {
	for s := range m.g {
		m.g[s].Init(m.seed)
		m.seen[s] = m.g[s].Stats().Event
		m.sent[s] = 0
	}
	m.roundOver, m.draw, m.winner = false, false, Left
}
