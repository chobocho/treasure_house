package core

import "testing"

func TestNewStartsInAPlayableState(t *testing.T) {
	g := New(1)
	s := g.Stats()
	if s.State != StatePlay {
		t.Errorf("상태가 %d 다", s.State)
	}
	if s.Level != 1 {
		t.Errorf("레벨이 %d 다", s.Level)
	}
	if s.Combo != -1 {
		t.Errorf("콤보가 %d 다 — 시작값은 -1(콤보 없음) 이다", s.Combo)
	}
	if s.Hold != -1 {
		t.Errorf("홀드가 %d 다 — 비어 있어야 한다", s.Hold)
	}
	if s.Gravity != int32(GravityMs[1]) {
		t.Errorf("낙하 간격이 %d 다", s.Gravity)
	}
	if s.Pieces != 1 {
		t.Errorf("놓인 조각 수가 %d 다 — 첫 조각이 스폰됐으니 1 이어야 한다", s.Pieces)
	}
	if !g.Board().Empty() {
		t.Error("시작부터 판에 뭔가 있다")
	}
}

// 다음 큐는 늘 다섯 개가 보여야 한다. 그리고 조각을 하나 놓으면 한 칸씩 당겨진다.
func TestNextQueueAdvances(t *testing.T) {
	g := New(1)
	before := g.Next(5)
	if len(before) != 5 {
		t.Fatalf("다음 큐가 %d개다", len(before))
	}
	g.Press(ActHard)
	after := g.Next(5)
	for i := 0; i < 4; i++ {
		if after[i] != before[i+1] {
			t.Fatalf("큐가 한 칸 안 당겨졌다: %v → %v", before, after)
		}
	}
}

func TestHardDropLocksAndScores(t *testing.T) {
	g := New(1)
	before := g.Stats()
	g.Press(ActHard)
	s := g.Stats()
	if s.Score <= before.Score {
		t.Errorf("하드드롭 점수가 안 올랐다: %d → %d", before.Score, s.Score)
	}
	if s.Pieces != before.Pieces+1 {
		t.Errorf("조각 수가 %d → %d 다", before.Pieces, s.Pieces)
	}
	if s.Event != before.Event+1 {
		t.Error("락 이벤트 번호가 안 올랐다")
	}
	if g.Board().Empty() {
		t.Error("하드드롭했는데 판이 비어 있다")
	}
}

// 홀드는 조각당 한 번. 무한 스왑을 막는 규칙이다.
func TestHoldOncePerPiece(t *testing.T) {
	g := New(1)
	first := g.Stats().Piece
	g.Press(ActHold)
	if g.Stats().Hold != first {
		t.Errorf("홀드에 %d 가 들어갔다 — %d 여야 한다", g.Stats().Hold, first)
	}
	held := g.Stats().Hold
	second := g.Stats().Piece
	g.Press(ActHold) // 두 번째는 무시돼야 한다
	if g.Stats().Hold != held || g.Stats().Piece != second {
		t.Error("같은 조각으로 홀드를 두 번 했다")
	}
}

// 홀드가 비어 있으면 다음 조각을 꺼내 온다. 채워져 있으면 맞바꾼다.
func TestHoldSwapsWithStoredPiece(t *testing.T) {
	g := New(1)
	a := g.Stats().Piece
	g.Press(ActHold)
	b := g.Stats().Piece
	g.Press(ActHard) // 홀드 제한 해제
	g.Press(ActHold)
	if g.Stats().Piece != a {
		t.Errorf("맞바꾼 조각이 %d — 처음 넣어 둔 %d 가 나와야 한다", g.Stats().Piece, a)
	}
	if b == a {
		t.Skip("두 조각이 우연히 같아서 이 시드로는 확인할 수 없다")
	}
}

func TestMoveAndRotate(t *testing.T) {
	g := New(1)
	x0 := g.Stats().X
	g.Press(ActLeft)
	if g.Stats().X != x0-1 {
		t.Errorf("왼쪽으로 안 갔다: %d → %d", x0, g.Stats().X)
	}
	g.Press(ActRight)
	if g.Stats().X != x0 {
		t.Errorf("오른쪽으로 안 돌아왔다: %d", g.Stats().X)
	}
	r0 := g.Stats().Rot
	g.Press(ActCW)
	g.SetPiece(PieceT) // 회전 결과를 확실히 보려고 T 로 고정
	g.Press(ActCW)
	if g.Stats().Rot == r0 && Shapes[PieceT][0] != Shapes[PieceT][1] {
		t.Error("회전이 안 됐다")
	}
}

// 벽에 붙으면 더 못 간다. 좌표가 판 밖으로 나가면 안 된다.
func TestWallStopsMovement(t *testing.T) {
	g := New(1)
	g.SetPiece(PieceO)
	for i := 0; i < 20; i++ {
		g.Press(ActLeft)
	}
	if got := g.Stats().X; got != -1 {
		// O 조각의 왼쪽 열은 x+1 이므로 x = -1 에서 벽에 닿는다
		t.Errorf("왼쪽 끝에서 x=%d 다", got)
	}
	for i := 0; i < 20; i++ {
		g.Press(ActRight)
	}
	if got := g.Stats().X; got != W-3 {
		t.Errorf("오른쪽 끝에서 x=%d 다", got)
	}
}

func TestFlipIsTwoRotations(t *testing.T) {
	g := New(1)
	g.SetPiece(PieceT)
	g.Press(ActFlip)
	if got := g.Stats().Rot; got != 2 {
		t.Errorf("180도 회전 뒤 rot 이 %d 다", got)
	}
}

// 일시정지 중에는 시간도 조작도 멈춘다. 다시 누르면 풀린다.
func TestPauseFreezesEverything(t *testing.T) {
	g := New(1)
	g.Press(ActPause)
	if g.Stats().State != StatePause {
		t.Fatalf("상태가 %d 다", g.Stats().State)
	}
	x := g.Stats().X
	el := g.Stats().Elapsed
	g.Press(ActLeft)
	g.Update(500)
	if g.Stats().X != x {
		t.Error("일시정지 중에 조각이 움직였다")
	}
	if g.Stats().Elapsed != el {
		t.Error("일시정지 중에 시간이 흘렀다")
	}
	g.Press(ActPause)
	if g.Stats().State != StatePlay {
		t.Error("일시정지가 안 풀렸다")
	}
}

// 중력. 레벨 1 은 1000ms 마다 한 칸이다.
// 한 번에 1000ms 를 넣을 수 없다 — Update 는 dt 를 100ms 로 자른다(아래 테스트 참고).
func TestGravityDropsOneCellPerInterval(t *testing.T) {
	g := New(1)
	y := g.Stats().Y
	for i := 0; i < 9; i++ {
		g.Update(100) // 900ms
	}
	if g.Stats().Y != y {
		t.Errorf("900ms 만에 떨어졌다: %d → %d", y, g.Stats().Y)
	}
	g.Update(100) // 1000ms
	if g.Stats().Y != y+1 {
		t.Errorf("1000ms 뒤 y 가 %d — %d 를 기대했다", g.Stats().Y, y+1)
	}
}

// dt 상한. 탭을 전환했다 돌아와서 거대한 dt 가 들어와도 판이 순간이동하면 안 된다.
func TestHugeDeltaIsClamped(t *testing.T) {
	g := New(1)
	g.Update(100000)
	if got := g.Stats().Elapsed; got != 100 {
		t.Errorf("경과 시간이 %d — 100ms 로 잘려야 한다", got)
	}
}

// 락다운 유예: 바닥에 닿아도 500ms 동안은 안 굳는다.
func TestLockDelay(t *testing.T) {
	g := New(1)
	g.SetPiece(PieceO)
	g.Press(ActSoft)
	for i := 0; i < 30; i++ { // 소프트드롭으로 바닥까지 가라앉힌다
		g.Update(100)
		if g.Stats().LockPct > 0 {
			break
		}
	}
	if g.Stats().LockPct == 0 {
		t.Fatal("바닥에 닿지 않았다")
	}
	pieces := g.Stats().Pieces
	g.Update(100)
	if g.Stats().Pieces != pieces {
		t.Error("유예가 끝나기 전에 굳었다")
	}
	for i := 0; i < 6; i++ {
		g.Update(100)
	}
	if g.Stats().Pieces == pieces {
		t.Error("유예가 지났는데 안 굳었다")
	}
}

// 블록아웃: 스폰 자리가 이미 막혀 있으면 게임 오버.
func TestBlockOut(t *testing.T) {
	g := New(1)
	g.Paint(rep("##########", Vis+Hidden))
	g.SetPiece(PieceO)
	if g.Stats().State != StateOver {
		t.Errorf("꽉 찬 판인데 상태가 %d 다", g.Stats().State)
	}
}

func TestGameOverIgnoresInput(t *testing.T) {
	g := New(1)
	g.Paint(rep("##########", Vis+Hidden))
	g.SetPiece(PieceO)
	x := g.Stats().X
	g.Press(ActLeft)
	g.Update(1000)
	if g.Stats().X != x {
		t.Error("게임 오버 뒤에도 조작이 먹는다")
	}
}

// 줄 지우기와 점수. 판을 심어 두고 I 를 세워 꽂으면 테트리스가 난다.
func TestTetrisScoresAndClears(t *testing.T) {
	g := New(1)
	// 우물 4줄 아래에 "안 지워지는 바닥줄"을 깐다.
	// 이게 없으면 판이 통째로 비워져 퍼펙트 클리어가 되고, 공격이 +10 붙는다.
	g.Paint(append(rep(".#########", 4), "#########."))
	g.SetPiece(PieceI)
	g.Press(ActCW)
	for i := 0; i < 6; i++ {
		g.Press(ActLeft)
	}
	g.Press(ActHard)
	s := g.Stats()
	if s.Clear != 4 {
		t.Fatalf("지운 줄이 %d 다:\n%v", s.Clear, g.Board().Rows()[Vis-6:])
	}
	if s.Lines != 4 {
		t.Errorf("누적 줄이 %d 다", s.Lines)
	}
	// 테트리스 800 × 레벨 1 + 콤보 50×0 + 하드드롭 낙하 점수
	if s.Gain < 800 {
		t.Errorf("획득 점수가 %d 다", s.Gain)
	}
	if s.B2B != 1 {
		t.Error("테트리스인데 B2B 가 안 켜졌다")
	}
	if s.Attack != 4 {
		t.Errorf("공격이 %d줄이다 — 테트리스는 4줄이다", s.Attack)
	}
}

// 대기 가비지는 "줄을 못 지운 락"에서만 솟아오른다.
// 이 유예가 없으면 상쇄할 기회 자체가 사라진다.
func TestPendingGarbageRisesOnlyOnANonClearingLock(t *testing.T) {
	g := New(1)
	g.QueueGarbage(3)
	if g.Stats().Pending != 3 {
		t.Fatalf("대기 줄이 %d 다", g.Stats().Pending)
	}
	g.SetPiece(PieceO)
	g.Press(ActHard) // 줄이 안 지워지는 락
	if g.Stats().Pending != 0 {
		t.Errorf("대기 줄이 %d 남았다", g.Stats().Pending)
	}
	if g.Stats().GarbageRecv != 3 {
		t.Errorf("받은 가비지가 %d줄이다", g.Stats().GarbageRecv)
	}
}

// 상쇄: 내가 보낼 공격이 먼저 내 대기줄을 지운다.
func TestAttackCancelsPendingGarbage(t *testing.T) {
	g := New(1)
	g.Paint(append(rep(".#########", 4), "#########."))
	g.QueueGarbage(2)
	g.SetPiece(PieceI)
	g.Press(ActCW)
	for i := 0; i < 6; i++ {
		g.Press(ActLeft)
	}
	g.Press(ActHard) // 테트리스 = 공격 4줄
	s := g.Stats()
	if s.Pending != 0 {
		t.Errorf("상쇄 뒤 대기 줄이 %d 다", s.Pending)
	}
	if s.Attack != 2 {
		t.Errorf("상대에게 %d줄 갔다 — 4−2 = 2줄이어야 한다", s.Attack)
	}
	if s.GarbageRecv != 0 {
		t.Error("상쇄했는데 가비지가 올라왔다")
	}
}

// 한 번에 올라오는 줄에는 상한이 있다. 없으면 20줄이 한꺼번에 솟아 즉사한다.
func TestGarbageRiseIsCapped(t *testing.T) {
	g := New(1)
	g.QueueGarbage(20)
	g.SetPiece(PieceO)
	g.Press(ActHard)
	if got := g.Stats().GarbageRecv; got != GarbageCap {
		t.Errorf("한 번에 %d줄이 올라왔다 — 상한은 %d줄이다", got, GarbageCap)
	}
	if got := g.Stats().Pending; got != 20-GarbageCap {
		t.Errorf("대기 줄이 %d 다", got)
	}
}

func TestPushGarbageDirectly(t *testing.T) {
	g := New(1)
	g.PushGarbage(2, 3)
	if g.Board().At(3, H-1) != 0 {
		t.Error("지정한 구멍이 안 뚫렸다")
	}
	if g.Board().At(4, H-1) != Garbage {
		t.Error("가비지가 안 올라왔다")
	}
}

// Init 은 판을 완전히 처음 상태로 되돌린다. 새 시드면 조각 순서도 달라진다.
func TestInitResets(t *testing.T) {
	g := New(1)
	g.Press(ActHard)
	g.Press(ActHard)
	g.Init(2)
	s := g.Stats()
	if s.Score != 0 || s.Lines != 0 || s.Pieces != 1 || s.State != StatePlay {
		t.Errorf("초기화가 덜 됐다: %+v", s)
	}
	if !g.Board().Empty() {
		t.Error("판이 안 비었다")
	}
}

// 같은 시드는 같은 판. 이게 무너지면 골든 트레이스가 성립하지 않는다.
func TestSameSeedSameGame(t *testing.T) {
	run := func() uint32 {
		g := New(777)
		for i := 0; i < 30; i++ {
			g.Press(ActCW)
			g.Press(ActLeft)
			g.Press(ActHard)
			g.Update(37)
		}
		return BoardHash(g.Board())
	}
	if run() != run() {
		t.Error("같은 시드로 두 번 돌렸는데 판이 다르다")
	}
}

// Cells 와 Overlay 는 화면이 읽는 두 층이다. 고스트는 현재 조각 아래에 있어야 한다.
func TestOverlayHasPieceAndGhost(t *testing.T) {
	g := New(1)
	ov := g.Overlay()
	if len(ov) != Vis*W {
		t.Fatalf("오버레이가 %d칸이다", len(ov))
	}
	var piece, ghost int
	for _, v := range ov {
		switch {
		case v >= 1 && v <= 7:
			piece++
		case v >= 8:
			ghost++
		}
	}
	if piece != 4 {
		t.Errorf("현재 조각이 %d칸 그려졌다", piece)
	}
	if ghost == 0 {
		t.Error("고스트가 안 그려졌다")
	}
	if len(g.Cells()) != Vis*W {
		t.Errorf("굳은 블록 층이 %d칸이다", len(g.Cells()))
	}
}

// Pack 은 C++ 배열 순서를 되살린다. 순서가 틀리면 골든 트레이스의 stats 해시가
// 통째로 어긋나므로, 몇 자리를 직접 짚어 못 박아 둔다.
func TestStatsPackOrder(t *testing.T) {
	s := Stats{Score: 11, Lines: 22, Level: 3, Combo: -1, Hold: -1,
		Next: [5]int32{1, 2, 3, 4, 5}, Gravity: 1000, GarbageRecv: 9}
	p := s.Pack()
	if len(p) != StatCount {
		t.Fatalf("배열이 %d칸이다", len(p))
	}
	for i, want := range map[int]int32{0: 11, 1: 22, 2: 3, 3: -1, 6: -1,
		7: 1, 11: 5, 17: 1000, 29: 9} {
		if p[i] != want {
			t.Errorf("배열 %d번이 %d — %d 를 기대했다", i, p[i], want)
		}
	}
}

func TestStatsHashChanges(t *testing.T) {
	a := Stats{Score: 1}
	b := Stats{Score: 2}
	if StatsHash(a) == StatsHash(b) {
		t.Error("점수가 다른데 해시가 같다")
	}
}

// ── AI 층이 쓰는 접근자 ────────────────────────────────────────────────

func TestCurrentPieceAndHoldAccessors(t *testing.T) {
	g := New(1)
	if g.CurrentPiece() != int(g.Stats().Piece) {
		t.Errorf("CurrentPiece 가 %d — stats 는 %d 다", g.CurrentPiece(), g.Stats().Piece)
	}
	p, used := g.Hold()
	if p != -1 || used {
		t.Errorf("시작 홀드가 (%d, %v) 다 — (-1, false) 여야 한다", p, used)
	}
	first := g.CurrentPiece()
	g.Press(ActHold)
	p, used = g.Hold()
	if p != first || !used {
		t.Errorf("홀드 뒤가 (%d, %v) 다 — (%d, true) 여야 한다", p, used, first)
	}
}

// DropAt 은 AI 전용 지름길이다. 회전과 x 를 지정해 곧바로 굳힌다.
// 규칙을 우회하지는 않는다 — 낙하와 락은 하드드롭 경로를 그대로 쓴다.
func TestDropAtPlacesAndLocks(t *testing.T) {
	g := New(1)
	g.SetPiece(PieceO)
	pieces := g.Stats().Pieces
	g.DropAt(0, 6)
	if g.Stats().Pieces != pieces+1 {
		t.Error("DropAt 이 조각을 안 굳혔다")
	}
	// O 조각은 x+1, x+2 열을 차지한다 → 바닥 두 줄의 7·8열이 차 있어야 한다
	if g.Board().At(7, H-1) == 0 || g.Board().At(8, H-1) == 0 {
		t.Errorf("지정한 자리에 안 놓였다:\n%v", g.Board().Rows()[Vis-3:])
	}
}

// 놓을 수 없는 자리를 주면 회전·이동을 하지 않고 그 자리에서 떨어뜨린다.
// (원본 ai_apply 와 같은 처리 — AI 가 이상한 수를 줘도 판이 깨지지 않는다)
func TestDropAtIgnoresImpossiblePlacement(t *testing.T) {
	g := New(1)
	g.SetPiece(PieceO)
	g.DropAt(0, 99)
	if x := g.Stats().X; x < -3 || x > W {
		t.Errorf("조각이 판 밖으로 나갔다: x=%d", x)
	}
	if g.Stats().Pieces < 2 {
		t.Error("그래도 굳기는 해야 한다")
	}
}

// DropAt 은 회전으로 들어간 게 아니므로 T스핀으로 세면 안 된다.
func TestDropAtIsNotATSpin(t *testing.T) {
	g := New(1)
	g.Paint(append([]string{"..#..#....", "###...####", "####.#####"}, rep("#########.", 15)...))
	g.SetPiece(PieceT)
	g.DropAt(2, 3)
	if g.Stats().TSpin != TSpinNone {
		t.Errorf("T스핀 %d 로 잡혔다 — DropAt 은 회전이 아니다", g.Stats().TSpin)
	}
}
