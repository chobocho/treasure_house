package ai

import "treasure/tetris_tui/core"

// Move 는 AI 가 고른 한 수.
type Move struct {
	UseHold bool
	Rot     int
	X       int
}

// Pack 은 한 수를 정수 하나로 접는다: (useHold << 8) | (rot << 4) | (x + 3).
//
// x 에 +3 을 더하는 건 −3 까지 가능한 좌표를 4비트 무부호로 담기 위해서다.
// (조각이 왼쪽 벽에 붙으려면 4×4 상자의 왼쪽 끝이 판 밖으로 나가야 한다)
//
// 왜 접는가. 1편의 wasm 은 구조체를 반환할 수 없어서 정수 하나로 접었다.
// Go 에서는 구조체를 그냥 돌려주면 되지만, 골든 트레이스가 이 접힌 값으로
// 기록돼 있어서 대조하려면 같은 방식으로 접을 수 있어야 한다.
func (m Move) Pack() int {
	h := 0
	if m.UseHold {
		h = 1
	}
	return h<<8 | (m.Rot&3)<<4 | (m.X+3)&15
}

// Unpack 은 Pack 의 역. 음수는 "둘 수 없음"이다.
func Unpack(packed int) (Move, bool) {
	if packed < 0 {
		return Move{}, false
	}
	return Move{
		UseHold: packed>>8&1 == 1,
		Rot:     packed >> 4 & 3,
		X:       packed&15 - 3,
	}, true
}

// Searcher 는 탐색용 판 사본을 재사용한다.
//
// 후보 하나마다 240바이트짜리 판을 새로 할당하면 한 수에 100번 가까이 할당이 일어나고,
// 그게 AI vs AI 400조각 × 두 판이면 수만 번이 된다. 구조체 하나를 들고 다니면 0번이다.
// (그래서 Best 는 값이 아니라 포인터 리시버다)
type Searcher struct {
	sim core.Board
}

// simDrop 은 (rot, x) 로 스폰 줄에서 곧장 떨어뜨렸을 때 멈추는 y. 스폰 줄이 막혀 있으면 -1.
func simDrop(b *core.Board, piece, rot, x int) int {
	if b.Collide(piece, rot, x, core.SpawnY) {
		return -1
	}
	return b.DropY(piece, rot, x, core.SpawnY)
}

// simReachable 은 스폰 자리에서 목표 x 까지 스폰 줄을 따라 한 칸씩 미끄러질 수 있는지 본다.
//
// AI가 고른 수를 나중에 *실제 키 입력*으로 재현해야 하므로, 도달 불가능한 자리를
// 후보에서 빼 둔다. 끼워 넣기(tuck)와 스핀은 이 탐색의 범위 밖이다 —
// 그래서 이 AI 는 T스핀을 노리지 않는다. 정직하게 말해 두는 편이 낫다.
func simReachable(b *core.Board, piece, rot, x int) bool {
	if b.Collide(piece, rot, core.SpawnX, core.SpawnY) {
		return false
	}
	step := -1
	if x > core.SpawnX {
		step = 1
	}
	for cx := core.SpawnX; cx != x; cx += step {
		if b.Collide(piece, rot, cx+step, core.SpawnY) {
			return false
		}
	}
	return true
}

// Snapshot 은 탐색에 필요한 판 상태를 통째로 떼어 낸 사본이다.
//
// 왜 필요한가. 7부에서 AI 의 탐색은 Update 바깥의 **다른 고루틴**에서 돈다(Cmd).
// 그 고루틴이 진행 중인 *core.Game 을 들여다보면, 같은 순간 Update 가 그 판을
// 고치고 있을 수 있다 — 자료 경쟁이고, Go 의 레이스 검출기가 잡아 준다.
// 그래서 탐색을 시작하기 전에 필요한 것만 값으로 복사해 넘긴다.
//
// 판이 240바이트라 복사가 싸다. "공유하지 말고 복사하라"가 여기서는 성능 손해가 아니다.
type Snapshot struct {
	Board    core.Board
	Playing  bool
	Piece    int
	Hold     int
	HoldUsed bool
	Next     int
}

// SnapshotOf 는 지금 판의 사본을 뜬다. Update 안에서 부른다.
func SnapshotOf(g *core.Game) Snapshot {
	hold, used := g.Hold()
	next := g.Next(1)
	n := -1
	if len(next) > 0 {
		n = next[0]
	}
	return Snapshot{
		Board:    *g.Board(),
		Playing:  g.Stats().State == core.StatePlay,
		Piece:    g.CurrentPiece(),
		Hold:     hold,
		HoldUsed: used,
		Next:     n,
	}
}

// Best 는 지금 판에서 가장 좋은 한 수를 고른다. 사본을 떠서 BestOf 에 넘긴다.
func (s *Searcher) Best(g *core.Game, w Weights) (Move, [FCount]float32, bool) {
	return s.BestOf(SnapshotOf(g), w)
}

// BestOf 는 사본 위에서 가장 좋은 한 수를 고른다.
//
// 후보 = (홀드 쓸까 말까) × (회전 4) × (x −3‥9) ≈ 최대 104개, 실제 유효한 건 30~80개.
// 1수 앞만 본다. 2수 앞을 보면 후보가 1만 개로 늘고, TUI 의 한 프레임 안에 안 끝난다.
//
// 동점 처리가 중요하다: `s > best` 로 비교하므로 **먼저 본 후보가 이긴다**.
// 이 규칙이 다르면 가중치가 같아도 다른 수가 나오고, 판이 통째로 갈라진다.
func (s *Searcher) BestOf(snap Snapshot, w Weights) (Move, [FCount]float32, bool) {
	var feat [FCount]float32
	if !snap.Playing {
		return Move{}, feat, false
	}
	board := &snap.Board

	var best Move
	var bestScore float32
	have := false

	for useHold := 0; useHold < 2; useHold++ {
		var piece int
		if useHold == 0 {
			piece = snap.Piece
		} else {
			if snap.HoldUsed {
				continue // 조각당 홀드 1회
			}
			// 홀드가 비어 있으면 홀드는 "다음 조각을 당겨 오는" 동작이 된다.
			piece = snap.Hold
			if piece < 0 {
				piece = snap.Next
			}
		}
		for rot := 0; rot < 4; rot++ {
			// O 조각처럼 회전해도 모양이 같으면 같은 후보를 네 번 보게 된다.
			if rot > 0 && core.Shapes[piece][rot] == core.Shapes[piece][0] {
				continue
			}
			for x := -3; x < core.W; x++ {
				y := simDrop(board, piece, rot, x)
				if y < 0 {
					continue
				}
				if !simReachable(board, piece, rot, x) {
					continue
				}

				s.sim = *board // 240바이트 값 복사 — 진행 중인 판은 절대 안 건드린다
				s.sim.Place(piece, rot, x, y)
				landH := core.H - (y + core.ShapeBottom(piece, rot)) // 바닥줄 = 1
				lines, _ := s.sim.ClearLines()
				f := Features(&s.sim, lines, landH)
				sc := Score(w, f)

				if !have || sc > bestScore {
					have, bestScore = true, sc
					best = Move{UseHold: useHold == 1, Rot: rot, X: x}
					feat = f
				}
			}
		}
	}
	return best, feat, have
}

// Apply 는 고른 수를 실제 판에 둔다.
//
// 규칙을 우회하지 않는다 — 홀드는 홀드 규칙을, 낙하는 하드드롭 경로를 그대로 쓴다.
// AI 가 사람보다 유리한 규칙으로 노는 일이 없어야 대전이 성립한다.
func Apply(g *core.Game, m Move) {
	if g.Stats().State != core.StatePlay {
		return
	}
	if m.UseHold {
		g.Press(core.ActHold)
		if g.Stats().State != core.StatePlay {
			return
		}
	}
	g.DropAt(m.Rot, m.X)
}

// EvalHere 는 지금 판을 그대로(조각을 놓지 않고) 평가한다 — 숫자를 눈으로 보는 슬라이드용.
func EvalHere(g *core.Game, w Weights) (float32, [FCount]float32) {
	f := Features(g.Board(), 0, 0)
	return Score(w, f), f
}

// PlayResult 는 한 판을 끝까지 둔 결과.
type PlayResult struct {
	Lines  int
	Attack int
	Placed int
	Game   *core.Game
}

// Play 는 한 판을 끝까지(또는 maxPieces 개까지) 둔다.
//
// every > 0 이면 그만큼 놓을 때마다 가비지 1줄이 예약된다 — "비가 새는 배" 모드다.
// 왜 이게 필요한가: 가비지가 없으면 웬만한 가중치도 400조각을 안 죽고 버틴다.
// 전원이 만점을 받으면 어느 쪽이 더 나은지 구별할 수가 없다(적합도 천장).
func Play(w Weights, seed uint32, maxPieces, every int) PlayResult {
	g := core.New(seed)
	var s Searcher
	r := PlayResult{Game: g}

	for g.Stats().State == core.StatePlay && r.Placed < maxPieces {
		if every > 0 && r.Placed > 0 && r.Placed%every == 0 {
			g.QueueGarbage(1)
		}
		m, _, ok := s.Best(g, w)
		if !ok {
			break
		}
		Apply(g, m)
		r.Attack += int(g.Stats().Attack)
		r.Placed++
	}
	r.Lines = int(g.Stats().Lines)
	return r
}
