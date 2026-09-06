package ai

import (
	"testing"

	"treasure/tetris_tui/core"
)

func TestPackRoundTrip(t *testing.T) {
	for _, m := range []Move{
		{UseHold: false, Rot: 0, X: -3},
		{UseHold: false, Rot: 3, X: 9},
		{UseHold: true, Rot: 2, X: 0},
	} {
		p := m.Pack()
		if p < 0 {
			t.Fatalf("%+v 가 음수 %d 로 접혔다 — 음수는 '둘 수 없음'이다", m, p)
		}
		back, ok := Unpack(p)
		if !ok || back != m {
			t.Errorf("%+v → %d → %+v (ok=%v)", m, p, back, ok)
		}
	}
}

func TestUnpackNegativeMeansNoMove(t *testing.T) {
	if _, ok := Unpack(-1); ok {
		t.Error("-1 이 유효한 수로 풀렸다")
	}
}

// 빈 판에서는 반드시 둘 곳이 있다. 그리고 고른 자리가 판 안이어야 한다.
func TestBestFindsAMoveOnAnEmptyBoard(t *testing.T) {
	g := core.New(1)
	w, _ := Level("max")
	var s Searcher
	m, f, ok := s.Best(g, w)
	if !ok {
		t.Fatal("빈 판인데 둘 수가 없다고 한다")
	}
	if m.Rot < 0 || m.Rot > 3 {
		t.Errorf("회전이 %d 다", m.Rot)
	}
	if m.X < -3 || m.X >= core.W {
		t.Errorf("x 가 %d 다", m.X)
	}
	if f[FLand] <= 0 {
		t.Errorf("착지 높이가 %v 다 — 바닥줄이 1 이므로 1 이상이어야 한다", f[FLand])
	}
}

// 스폰 자리까지 꽉 찬 판에서는 둘 수가 없다.
func TestBestReturnsNothingWhenBlocked(t *testing.T) {
	g := core.New(1)
	g.Paint(rep("#########.", 20))
	g.SetPiece(core.PieceO)
	var s Searcher
	if _, _, ok := s.Best(g, Weights{}); ok {
		t.Error("스폰이 막혔는데 둘 수가 있다고 한다")
	}
}

// 게임 오버 상태에서는 탐색하지 않는다.
func TestBestReturnsNothingWhenGameOver(t *testing.T) {
	g := core.New(1)
	g.Paint(rep("##########", core.H))
	g.SetPiece(core.PieceO)
	var s Searcher
	if _, _, ok := s.Best(g, Weights{}); ok {
		t.Error("게임 오버인데 탐색이 됐다")
	}
}

// 탐색은 판을 건드리면 안 된다. 사본 위에서만 시뮬레이션한다.
// (1편의 어트랙트 봇이 못 했던 게 바로 이거다)
func TestBestDoesNotMutateTheBoard(t *testing.T) {
	g := core.New(1)
	g.Paint(rep("#########.", 6))
	before := core.BoardHash(g.Board())
	beforeStats := g.Stats()
	w, _ := Level("hard")
	var s Searcher
	s.Best(g, w)
	if core.BoardHash(g.Board()) != before {
		t.Error("탐색이 판을 바꿨다")
	}
	if g.Stats() != beforeStats {
		t.Error("탐색이 stats 를 바꿨다")
	}
}

// 도달 가능성: 스폰 줄을 따라 옆으로 미끄러져 갈 수 없는 자리는 후보가 아니다.
// 끼워 넣기(tuck)와 스핀은 이 탐색의 범위 밖이라고 정직하게 말해 두는 부분이다.
//
// 스폰 줄(y = Hidden)의 오른쪽 끝 세 칸을 막아 둔다. 스폰 자리 자체는 비어 있으므로
// 조각은 나오지만, 오른쪽으로는 어느 지점부터 미끄러져 갈 수 없다.
func TestReachabilityStopsAtABlockedSpawnRow(t *testing.T) {
	rows := make([]string, core.Vis)
	for i := range rows {
		rows[i] = ".........."
	}
	rows[0] = ".......###" // 스폰 줄: x = 7,8,9 가 막혀 있다
	var b core.Board
	b.Paint(rows)

	// O 조각은 x+1, x+2 열을 차지한다.
	//   x = 4 → 5,6열 … 통과
	//   x = 5 → 6,7열 … 7열이 막혀 있다
	for _, c := range []struct {
		x    int
		want bool
	}{{-1, true}, {0, true}, {3, true}, {4, true}, {5, false}, {7, false}} {
		if got := simReachable(&b, core.PieceO, 0, c.x); got != c.want {
			t.Errorf("x=%d 도달 가능이 %v — %v 를 기대했다", c.x, got, c.want)
		}
	}

	// 탐색이 고른 수도 도달 가능해야 한다.
	// 조각마다 모양이 차지하는 줄이 달라서 "x 가 4 이하"로는 못 잡는다
	// (I 조각의 rot0 은 스폰 줄이 아니라 그 아래 줄을 차지한다).
	// 그래서 고른 수의 조각을 다시 알아내 도달 가능성을 직접 계산해 본다.
	g := core.New(1)
	g.Paint(rows)
	g.SetPiece(core.PieceO)
	w, _ := Level("max")
	var s Searcher
	m, _, ok := s.Best(g, w)
	if !ok {
		t.Fatal("스폰은 비어 있는데 둘 수가 없다고 한다")
	}
	piece := g.CurrentPiece()
	if m.UseHold {
		if h, _ := g.Hold(); h >= 0 {
			piece = h
		} else {
			piece = g.Next(1)[0]
		}
	}
	if !simReachable(g.Board(), piece, m.Rot, m.X) {
		t.Errorf("도달할 수 없는 수를 골랐다: %s rot%d x=%d",
			core.PieceNames[piece], m.Rot, m.X)
	}
}

// 스폰 자리 자체가 막혀 있으면 어떤 x 도 도달 불가다.
func TestNothingIsReachableWhenSpawnIsBlocked(t *testing.T) {
	var b core.Board
	b.Paint(rep("##########", core.Vis))
	for _, x := range []int{-1, 0, 3, 6} {
		if simReachable(&b, core.PieceO, 0, x) {
			t.Errorf("스폰이 막혔는데 x=%d 가 도달 가능이다", x)
		}
	}
}

// 가중치가 전부 0 이면 모든 후보가 동점이다. 그때는 **첫 후보**가 뽑혀야 한다
// (원본이 `s > best_s` 로 비교하므로 동점은 앞선 것이 이긴다).
// 이 동점 처리가 다르면 판이 통째로 갈라진다.
func TestTiesGoToTheFirstCandidate(t *testing.T) {
	g := core.New(1)
	var s Searcher
	a, _, ok := s.Best(g, Weights{})
	if !ok {
		t.Fatal("둘 수가 없다")
	}
	b, _, _ := s.Best(g, Weights{})
	if a != b {
		t.Errorf("같은 판에서 두 번 탐색했는데 %+v 와 %+v 로 갈렸다", a, b)
	}
	// 첫 후보는 홀드 안 씀 · rot 0 · 가장 왼쪽에서 유효한 x 다.
	if a.UseHold {
		t.Error("동점인데 홀드를 썼다")
	}
	if a.Rot != 0 {
		t.Errorf("동점인데 rot 이 %d 다", a.Rot)
	}
}

// 가중치가 실제로 선택을 바꾼다. 착지 높이(F_LAND)의 부호만 뒤집어 확인한다:
// +면 높은 곳을, −면 낮은 곳을 좋아해야 한다.
//
// 판은 왼쪽 절반만 10줄 높이로 쌓은 것. 왼쪽에 놓으면 착지 높이 11, 오른쪽이면 1 이다.
func TestWeightSignChangesTheChoice(t *testing.T) {
	newGame := func() *core.Game {
		g := core.New(1)
		g.Paint(rep("#####.....", 10))
		g.SetPiece(core.PieceO)
		return g
	}
	high := Weights{}
	high[FLand] = 1 // 높은 곳을 좋아함
	low := Weights{}
	low[FLand] = -1 // 낮은 곳을 좋아함

	var s Searcher
	a, fa, ok1 := s.Best(newGame(), high)
	b, fb, ok2 := s.Best(newGame(), low)
	if !ok1 || !ok2 {
		t.Fatal("둘 수가 없다")
	}
	if fa[FLand] <= fb[FLand] {
		t.Errorf("착지 높이가 %v(높은 쪽 선호) vs %v(낮은 쪽 선호) — 앞이 더 커야 한다",
			fa[FLand], fb[FLand])
	}
	if a.X == b.X {
		t.Errorf("두 가중치가 같은 x=%d 를 골랐다", a.X)
	}
}

// Apply 는 규칙을 우회하지 않는다 — 홀드는 홀드 규칙을, 낙하는 하드드롭을 그대로 쓴다.
func TestApplyPlacesThePiece(t *testing.T) {
	g := core.New(1)
	pieces := g.Stats().Pieces
	Apply(g, Move{Rot: 0, X: 4})
	if g.Stats().Pieces != pieces+1 {
		t.Error("Apply 가 조각을 안 굳혔다")
	}
	if g.Board().Empty() {
		t.Error("판이 비어 있다")
	}
}

func TestApplyUsesHold(t *testing.T) {
	g := core.New(1)
	first := g.CurrentPiece()
	Apply(g, Move{UseHold: true, Rot: 0, X: 3})
	if p, _ := g.Hold(); p != first {
		t.Errorf("홀드에 %d 가 들어갔다 — %d 여야 한다", p, first)
	}
}

func TestEvalHereDoesNotPlaceAnything(t *testing.T) {
	g := core.New(1)
	g.Paint(rep("#########.", 5))
	before := core.BoardHash(g.Board())
	w, _ := Level("max")
	score, f := EvalHere(g, w)
	if core.BoardHash(g.Board()) != before {
		t.Error("EvalHere 가 판을 바꿨다")
	}
	if f[FLines] != 0 || f[FLand] != 0 {
		t.Errorf("조각을 안 놨는데 lines=%v land=%v 다", f[FLines], f[FLand])
	}
	if score == 0 {
		t.Error("점수가 0 이다 — 특징이 하나도 안 잡혔다")
	}
}

// 한 판 통째로 두기. max 가중치라면 400조각을 놓는 동안 꽤 많은 줄을 지워야 한다.
func TestPlayFullGame(t *testing.T) {
	w, _ := Level("max")
	r := Play(w, 1, 400, 0)
	if r.Placed == 0 {
		t.Fatal("조각을 하나도 안 놨다")
	}
	if r.Lines == 0 {
		t.Error("줄을 하나도 못 지웠다")
	}
	if r.Game == nil {
		t.Fatal("게임이 nil 이다")
	}
	if int(r.Game.Stats().Lines) != r.Lines {
		t.Errorf("반환한 줄 수 %d 와 stats 의 %d 가 다르다", r.Lines, r.Game.Stats().Lines)
	}
	t.Logf("max 가중치 · 시드 1 · 400조각 — %d줄, 공격 %d, 놓은 조각 %d",
		r.Lines, r.Attack, r.Placed)
}

// "비가 새는 배" 모드: every 조각마다 가비지 1줄이 예약된다.
// 가비지가 없으면 웬만한 가중치도 400조각을 안 죽고 버텨서 우열을 못 가린다.
func TestPlayWithLeakIsHarder(t *testing.T) {
	w, _ := Level("max")
	dry := Play(w, 1, 400, 0)
	leak := Play(w, 1, 400, 12)
	if leak.Game.Stats().GarbageRecv == 0 {
		t.Error("가비지가 한 줄도 안 올라왔다")
	}
	t.Logf("가비지 없음 %d줄 / every=12 %d줄", dry.Lines, leak.Lines)
}

// 같은 설정이면 같은 결과. AI 는 난수를 쓰지 않는다.
func TestPlayIsDeterministic(t *testing.T) {
	w, _ := Level("normal")
	a := Play(w, 3, 120, 0)
	b := Play(w, 3, 120, 0)
	if a.Lines != b.Lines || a.Attack != b.Attack || a.Placed != b.Placed {
		t.Errorf("같은 설정인데 결과가 다르다: %+v vs %+v", a, b)
	}
	if core.BoardHash(a.Game.Board()) != core.BoardHash(b.Game.Board()) {
		t.Error("최종 판이 다르다")
	}
}
