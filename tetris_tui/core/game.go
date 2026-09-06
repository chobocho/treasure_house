package core

// Action 은 코어가 받는 조작 하나. 키 이름이 아니라 **뜻**이다.
//
// 왜 키가 아니라 뜻인가. 1인용은 화살표, 2인용의 왼쪽 자리는 WASD, AI 는 아예
// 키를 안 누른다. 이 셋이 전부 같은 규칙 위에서 돌려면 코어는 "왼쪽 키"가 아니라
// "왼쪽으로"만 알아야 한다. 키 배치는 ui 패키지의 일이다.
type Action int

const (
	ActLeft Action = iota
	ActRight
	ActSoft
	ActCW
	ActCCW
	ActHard
	ActHold
	ActPause
	ActFlip
)

// 게임 상태.
const (
	StatePlay  = 0
	StateOver  = 1
	StatePause = 2
)

// Stats 는 화면과 테스트가 읽는 숫자 상태 전부다.
//
// C++ 코어에서는 이게 int 배열 하나였다 — JS 와 선형 메모리를 공유해야 했으므로
// "인덱스가 곧 프로토콜"이었다. Go 에는 그런 제약이 없으니 이름 있는 구조체로 편다.
// 다만 필드 **순서**는 원본 배열 그대로 두었다. Pack() 이 그 배열을 되살려서
// 골든 트레이스의 stats 해시를 그대로 대조할 수 있어야 하기 때문이다.
type Stats struct {
	Score   int32
	Lines   int32
	Level   int32
	Combo   int32 // -1 = 콤보 없음, 0 = 첫 클리어, 1 = 2연속…
	B2B     int32 // 1 이면 다음 어려운 클리어에 ×1.5
	State   int32
	Hold    int32 // -1 = 비어 있음
	Next    [5]int32
	Clear   int32 // 이번 락으로 지운 줄
	TSpin   int32 // 0 없음 / 1 미니 / 2 정식
	Gain    int32 // 이번 락으로 얻은 점수
	Pieces  int32
	Elapsed int32 // 누적 ms
	Gravity int32
	Piece   int32
	Rot     int32
	X       int32
	Y       int32 // 보이는 판 기준 (숨은 줄을 뺀 값)
	Ghost   int32
	Event   int32 // 락이 일어날 때마다 1 증가 — 화면이 "새 사건"을 알아채는 수단
	RowMask int32
	Perfect int32
	LockPct int32 // 락다운 유예의 진행률 0~100

	Attack      int32 // 이번 락으로 상대에게 보낸 줄 수 (상쇄 후)
	Pending     int32 // 아직 올라오지 않고 대기 중인 가비지 줄 수
	GarbageRecv int32 // 지금까지 실제로 밀려 올라온 누적 줄 수
}

// StatCount 는 Pack() 이 만드는 배열의 길이. C++ 의 ST_COUNT 와 같아야 한다.
const StatCount = 30

// Pack 은 Stats 를 원본 C++ 의 배열 순서로 편다. 골든 트레이스 대조 전용이다.
//
// 손으로 나열하는 게 촌스러워 보이지만, 순서가 곧 계약이라 눈으로 읽히는 편이 낫다.
// (reflect 나 unsafe 로 자동화하면 필드를 하나 옮겼을 때 조용히 어긋난다)
func (s Stats) Pack() [StatCount]int32 {
	return [StatCount]int32{
		s.Score, s.Lines, s.Level, s.Combo, s.B2B, s.State, s.Hold,
		s.Next[0], s.Next[1], s.Next[2], s.Next[3], s.Next[4],
		s.Clear, s.TSpin, s.Gain, s.Pieces, s.Elapsed, s.Gravity,
		s.Piece, s.Rot, s.X, s.Y, s.Ghost, s.Event, s.RowMask,
		s.Perfect, s.LockPct, s.Attack, s.Pending, s.GarbageRecv,
	}
}

// StatsHash 는 Pack 결과의 FNV-1a 해시. 바이트는 32비트 리틀엔디언 순서로 먹인다 —
// JS 쪽 도구가 Int32Array 를 그렇게 훑기 때문이다. 음수도 2의 보수 그대로 들어간다.
func StatsHash(s Stats) uint32 {
	h := uint32(fnvOffset)
	for _, v := range s.Pack() {
		u := uint32(v)
		for b := 0; b < 4; b++ {
			h ^= u & 0xff
			h *= fnvPrime
			u >>= 8
		}
	}
	return h
}

// Game 은 판 하나. 2인용은 이걸 두 개 만들어 쓴다.
//
// 전역 상태가 하나도 없다는 점이 C++ 원본과의 가장 큰 차이다.
// 원본은 wasm 인스턴스 하나가 곧 판 하나였고, 두 판을 돌리려면 인스턴스를 두 개
// 띄워야 했다. Go 에서는 구조체를 두 개 만들면 끝이다.
type Game struct {
	board Board
	stats Stats

	cells   [Vis * W]uint8 // 화면용 굳은 블록
	overlay [Vis * W]uint8 // 화면용 현재 조각(1~7) · 고스트(8~14)

	rng *Rng
	bag *Bag

	cur       pieceState
	holdPiece int
	holdUsed  bool
	nextQ     [7]int

	gravAcc    int // 중력 누적 ms
	lockTimer  int
	lockResets int
	grounded   bool

	dasDir   int
	dasTimer int
	arrTimer int
	softHeld bool

	lastWasRot bool
	lastKick   int

	eventID        int
	pendingGarbage int
}

// pieceState 는 "지금 떨어지고 있는 조각"의 전부다.
type pieceState struct {
	piece, rot, x, y int
}

// New 는 시드로 새 판을 만든다.
func New(seed uint32) *Game {
	g := &Game{}
	g.Init(seed)
	return g
}

// Init 은 판을 처음 상태로 되돌린다. New 와 같은 일을 제자리에서 한다 —
// 게임오버 뒤 재시작이 새 할당 없이 끝나야 트레이스가 깔끔해진다.
func (g *Game) Init(seed uint32) {
	clear(g.board[:])
	g.stats = Stats{
		Level:   1,
		Combo:   -1,
		Hold:    -1,
		State:   StatePlay,
		Gravity: int32(GravityMs[1]),
	}
	g.rng = NewRng(seed)
	g.bag = NewBag(g.rng)
	g.holdPiece = -1
	g.holdUsed = false
	g.gravAcc, g.lockTimer, g.lockResets, g.grounded = 0, 0, 0, false
	g.dasDir, g.dasTimer, g.arrTimer, g.softHeld = 0, 0, 0, false
	g.lastWasRot, g.lastKick = false, 0
	g.eventID = 0
	g.pendingGarbage = 0

	for i := range g.nextQ {
		g.nextQ[i] = g.bag.Pull()
	}
	g.spawnNext()
	g.buildView()
}

// spawnNext 는 큐에서 조각 하나를 꺼내 스폰 자리에 놓는다.
func (g *Game) spawnNext() {
	g.cur.piece = g.nextQ[0]
	copy(g.nextQ[:6], g.nextQ[1:])
	g.nextQ[6] = g.bag.Pull()

	g.cur.rot = 0
	g.cur.x = SpawnX
	g.cur.y = SpawnY
	g.holdUsed = false
	g.grounded, g.lockTimer, g.lockResets = false, 0, 0
	g.lastWasRot, g.lastKick = false, 0
	g.stats.Pieces++

	// 블록아웃: 스폰 위치가 이미 막혔다 → 게임 오버
	if g.board.Collide(g.cur.piece, g.cur.rot, g.cur.x, g.cur.y) {
		g.stats.State = StateOver
	}
}

func (g *Game) tryMove(dx, dy int) bool {
	if g.board.Collide(g.cur.piece, g.cur.rot, g.cur.x+dx, g.cur.y+dy) {
		return false
	}
	g.cur.x += dx
	g.cur.y += dy
	g.lastWasRot = false
	return true
}

// tryRotate 는 다섯 킥 후보를 순서대로 밀어 보고 처음 성공한 곳에 앉힌다.
// dir: +1 = 시계, -1 = 반시계.
func (g *Game) tryRotate(dir int) bool {
	from := g.cur.rot
	to := (from + 3) & 3
	if dir > 0 {
		to = (from + 1) & 3
	}
	tbl := KickTable(g.cur.piece, dir, from)

	for k := 0; k < 5; k++ {
		nx := g.cur.x + int(tbl[k][0])
		ny := g.cur.y - int(tbl[k][1]) // ← y 부호 반전 (표는 위가 +)
		if !g.board.Collide(g.cur.piece, to, nx, ny) {
			g.cur.rot, g.cur.x, g.cur.y = to, nx, ny
			g.lastWasRot = true // T스핀 판정에 쓰인다
			g.lastKick = k      // 5번째(k == 4) 킥은 항상 정식 T스핀
			g.resetLockDelay()
			return true
		}
	}
	return false
}

// resetLockDelay 는 바닥에 닿은 채로 움직였을 때 유예를 되살린다.
// 되살릴 수 있는 횟수에 상한이 있어야 조각을 영원히 굴려 안 굳게 할 수 없다.
func (g *Game) resetLockDelay() {
	if g.grounded && g.lockResets < LockReset {
		g.lockTimer = 0
		g.lockResets++
	}
}

// detectTSpin 은 T 조각의 네 대각 코너를 세서 T스핀 종류를 가린다.
// 반환: TSpinNone / TSpinMini / TSpinFull
func (g *Game) detectTSpin() int {
	if g.cur.piece != PieceT || !g.lastWasRot {
		return TSpinNone
	}
	cx, cy := g.cur.x+1, g.cur.y+1
	count := func(tbl *[4][4]int8) int {
		n := 0
		if g.board.Filled(cx+int(tbl[g.cur.rot][0]), cy+int(tbl[g.cur.rot][1])) {
			n++
		}
		if g.board.Filled(cx+int(tbl[g.cur.rot][2]), cy+int(tbl[g.cur.rot][3])) {
			n++
		}
		return n
	}
	f, b := count(&tspinFront), count(&tspinBack)
	if f == 2 && b >= 1 {
		return TSpinFull
	}
	if f == 1 && b == 2 {
		if g.lastKick == 4 {
			return TSpinFull
		}
		return TSpinMini
	}
	return TSpinNone
}

// lockPiece 는 조각을 굳히고 줄을 지우고 점수·공격·가비지를 정산한 뒤 다음 조각을 낸다.
// 이 함수의 **순서**가 곧 대전 규칙이다 — 특히 공격 → 상쇄 → 솟아오름의 차례.
func (g *Game) lockPiece() {
	tsp := g.detectTSpin()
	g.board.Place(g.cur.piece, g.cur.rot, g.cur.x, g.cur.y)

	n, mask := g.board.ClearLines()
	lvl := int(g.stats.Level)
	b2bBefore := g.stats.B2B != 0 // 덮어쓰기 전에 붙잡아 둔다
	perfect := false

	base, difficult := LineScore(n, tsp)
	gain := base * lvl

	if n > 0 {
		if difficult && g.stats.B2B != 0 {
			gain = gain * 3 / 2 // Back-to-Back ×1.5
		}
		g.stats.B2B = 0
		if difficult {
			g.stats.B2B = 1
		}
		g.stats.Combo++ // -1 → 0(첫 클리어) → 1 → 2 …
		gain += 50 * int(g.stats.Combo) * lvl
		g.stats.Lines += int32(n)
		g.stats.Level = int32(LevelFor(int(g.stats.Lines)))

		if g.board.Empty() { // 퍼펙트 클리어
			gain += 1000 * lvl
			g.stats.Perfect++
			perfect = true
		}
	} else {
		g.stats.Combo = -1 // 콤보 끊김
	}

	g.stats.Score += int32(gain)
	g.stats.Gain = int32(gain)
	g.stats.Clear = int32(n)
	g.stats.TSpin = int32(tsp)
	g.stats.RowMask = int32(mask)
	g.stats.Gravity = int32(Gravity(int(g.stats.Level)))

	// 공격 계산 → 상쇄 → 가비지 적용. 순서가 규칙의 전부다.
	// 내가 보낼 공격은 먼저 *내* 대기줄을 지우고(상쇄), 남은 만큼만 상대에게 간다.
	// 그래서 맞받아치면 가비지가 올라오지 않는다.
	atk := Attack(n, tsp, b2bBefore, int(g.stats.Combo), perfect)
	cancel := atk
	if g.pendingGarbage < cancel {
		cancel = g.pendingGarbage
	}
	g.pendingGarbage -= cancel
	atk -= cancel
	g.stats.Attack = int32(atk)

	// 대기 중인 가비지는 "줄을 못 지운 락"에서만 실제로 솟아오른다.
	// 이 유예가 없으면 상쇄할 기회 자체가 없다.
	if n == 0 && g.pendingGarbage > 0 {
		k := g.pendingGarbage
		if k > GarbageCap {
			k = GarbageCap
		}
		g.pushRows(k, -1)
		g.pendingGarbage -= k
	}
	g.stats.Pending = int32(g.pendingGarbage)

	g.eventID++
	g.stats.Event = int32(g.eventID)

	g.spawnNext()
}

// pushRows 는 구멍 자리를 정해 판에 가비지를 밀어 올린다.
// hole < 0 이면 이 판의 RNG 가 고른다 — 두 구현이 같은 자리를 고르도록 코어 안에 둔다.
func (g *Game) pushRows(n, hole int) {
	if n <= 0 {
		return
	}
	if n > H {
		n = H
	}
	if hole < 0 || hole >= W {
		hole = g.rng.IntN(W)
	}
	g.board.PushRows(n, hole)
	g.stats.GarbageRecv += int32(n)
}

func (g *Game) hardDrop() {
	d := 0
	for g.tryMove(0, 1) {
		d++
	}
	g.stats.Score += int32(d * 2) // 하드드롭 1칸당 2점
	g.lockPiece()
}

func (g *Game) doHold() {
	if g.holdUsed {
		return // 조각당 1회 제한 — 무한 스왑 방지
	}
	p := g.holdPiece
	g.holdPiece = g.cur.piece
	g.stats.Hold = int32(g.holdPiece)
	if p < 0 {
		g.spawnNext()
	} else {
		g.cur = pieceState{piece: p, rot: 0, x: SpawnX, y: SpawnY}
		g.grounded, g.lockTimer, g.lockResets = false, 0, 0
		g.lastWasRot = false
		if g.board.Collide(g.cur.piece, g.cur.rot, g.cur.x, g.cur.y) {
			g.stats.State = StateOver
		}
	}
	g.holdUsed = true
}

// Press 는 조작 하나를 넣는다. 키를 누른 순간에 해당한다.
func (g *Game) Press(a Action) {
	if a == ActPause {
		switch g.stats.State {
		case StatePlay:
			g.stats.State = StatePause
		case StatePause:
			g.stats.State = StatePlay
		}
		return
	}
	if g.stats.State != StatePlay {
		return
	}

	switch a {
	case ActLeft, ActRight:
		d := -1
		if a == ActRight {
			d = 1
		}
		g.dasDir, g.dasTimer, g.arrTimer = d, 0, 0
		if g.tryMove(d, 0) {
			g.resetLockDelay()
		}
	case ActSoft:
		g.softHeld = true
		g.gravAcc = 0
	case ActCW:
		g.tryRotate(+1)
	case ActCCW:
		g.tryRotate(-1)
	case ActFlip:
		g.tryRotate(+1)
		g.tryRotate(+1)
	case ActHard:
		g.hardDrop()
	case ActHold:
		g.doHold()
	}
	g.buildView()
}

// Release 는 키를 뗀 순간. 터미널은 키를 뗀 것을 알려 주지 않으므로(7부 참고)
// TUI 판에서는 거의 쓰지 않지만, 골든 트레이스가 이 경로를 밟으므로 그대로 이식한다.
func (g *Game) Release(a Action) {
	switch {
	case a == ActLeft && g.dasDir < 0:
		g.dasDir = 0
	case a == ActRight && g.dasDir > 0:
		g.dasDir = 0
	case a == ActSoft:
		g.softHeld = false
	}
}

// Update 는 dtMs 만큼 시간을 진행시킨다. DAS/ARR → 중력 → 락다운 순서다.
func (g *Game) Update(dtMs int) {
	if g.stats.State != StatePlay {
		return
	}
	if dtMs > 100 {
		dtMs = 100 // 탭 전환 후 거대한 dt 방지
	}
	g.stats.Elapsed += int32(dtMs)

	// 1) DAS/ARR — 좌우 자동반복
	if g.dasDir != 0 {
		g.dasTimer += dtMs
		if g.dasTimer >= DasMs {
			g.arrTimer += dtMs
			for g.arrTimer >= ArrMs {
				g.arrTimer -= ArrMs
				if g.tryMove(g.dasDir, 0) {
					g.resetLockDelay()
				}
			}
		}
	}

	// 2) 중력 — 소프트드롭 중이면 20배 빠르게
	grav := Gravity(int(g.stats.Level))
	if g.softHeld {
		grav /= SoftDiv
		if grav < 1 {
			grav = 1
		}
	}
	g.gravAcc += dtMs
	for g.gravAcc >= grav {
		g.gravAcc -= grav
		before := g.cur.y
		g.tryMove(0, 1) // 실패해도 괜찮다 — 착지 판정은 아래에서 매번 한다
		if g.softHeld && g.cur.y > before {
			g.stats.Score++ // 소프트드롭 1칸 1점
		}
		if g.stats.State != StatePlay {
			return
		}
	}

	// 3) 락다운 — "닿아 있는가"를 중력 틱이 아니라 매 프레임 검사한다.
	//    중력 틱에서만 검사하면 레벨1(1000ms/칸)에서 착지 후 최대 1초를 그냥 서 있게 된다.
	if g.board.Collide(g.cur.piece, g.cur.rot, g.cur.x, g.cur.y+1) {
		g.grounded = true
		g.lockTimer += dtMs
		if g.lockTimer >= LockMs {
			g.lockPiece()
			g.gravAcc = 0
		}
	} else {
		g.grounded, g.lockTimer = false, 0 // 옆으로 빠져나가 다시 공중에 떴다
	}
	g.buildView()
}

// QueueGarbage 는 상대가 보낸 줄을 대기열에 넣는다. 실제로 솟아오르는 건
// "줄을 못 지운 락" 때다 — 그 유예가 있어야 맞받아쳐 상쇄할 기회가 생긴다.
func (g *Game) QueueGarbage(n int) {
	if n <= 0 {
		return
	}
	g.pendingGarbage += n
	g.stats.Pending = int32(g.pendingGarbage)
}

// PushGarbage 는 대기열을 거치지 않고 지금 당장 밀어 올린다. 테스트와 데모용.
// holeX < 0 이면 이 판의 RNG 가 고른다.
func (g *Game) PushGarbage(n, holeX int) {
	g.pushRows(n, holeX)
	// 진행 중인 조각이 솟아오른 줄에 파묻히면 위로 빼 준다.
	for g.board.Collide(g.cur.piece, g.cur.rot, g.cur.x, g.cur.y) && g.cur.y > -Hidden {
		g.cur.y--
	}
	if g.board.Collide(g.cur.piece, g.cur.rot, g.cur.x, g.cur.y) {
		g.stats.State = StateOver
	}
	g.buildView()
}

// SetPiece 는 지금 조각을 지정한 종류로 바꿔 스폰 상태로 되돌린다.
// 게임 로직은 절대 부르지 않는다 — 테스트에서 "이 조각이 지금 나와야 한다"를
// 강제할 방법이 필요해서 있는 훅이다.
func (g *Game) SetPiece(p int) {
	if p < 0 || p >= PieceCount {
		return
	}
	g.cur = pieceState{piece: p, rot: 0, x: SpawnX, y: SpawnY}
	g.holdUsed = false
	g.grounded, g.lockTimer, g.lockResets = false, 0, 0
	g.lastWasRot, g.lastKick = false, 0
	if g.board.Collide(g.cur.piece, g.cur.rot, g.cur.x, g.cur.y) {
		g.stats.State = StateOver
	}
	g.buildView()
}

// Paint 는 판을 문자열 그림으로 덮어쓴다. 테스트와 골든 트레이스 전용.
func (g *Game) Paint(rows []string) { g.board.Paint(rows) }

// buildView 는 화면이 읽는 두 층(cells, overlay)과 위치 관련 stats 를 새로 만든다.
// Update/Press 의 끝에서만 불린다 — 그려야 할 때가 곧 상태가 바뀐 직후다.
func (g *Game) buildView() {
	copy(g.cells[:], g.board[Hidden*W:])
	clear(g.overlay[:])

	if g.stats.State == StateOver {
		return
	}

	gy := g.board.DropY(g.cur.piece, g.cur.rot, g.cur.x, g.cur.y)
	for _, b := range Blocks(g.cur.piece, g.cur.rot) { // 고스트 먼저(현재 조각이 덮어쓴다)
		bx, by := g.cur.x+b[0], gy+b[1]-Hidden
		if by >= 0 && by < Vis && bx >= 0 && bx < W {
			g.overlay[by*W+bx] = uint8(g.cur.piece + 8)
		}
	}
	for _, b := range Blocks(g.cur.piece, g.cur.rot) {
		bx, by := g.cur.x+b[0], g.cur.y+b[1]-Hidden
		if by >= 0 && by < Vis && bx >= 0 && bx < W {
			g.overlay[by*W+bx] = uint8(g.cur.piece + 1)
		}
	}

	g.stats.Piece = int32(g.cur.piece)
	g.stats.Rot = int32(g.cur.rot)
	g.stats.X = int32(g.cur.x)
	g.stats.Y = int32(g.cur.y - Hidden)
	g.stats.Ghost = int32(gy - Hidden)
	for i := 0; i < 5; i++ {
		g.stats.Next[i] = int32(g.nextQ[i])
	}
	g.stats.LockPct = 0
	if g.grounded {
		g.stats.LockPct = int32(g.lockTimer * 100 / LockMs)
	}
}

// Stats 는 지금 숫자 상태의 사본.
func (g *Game) Stats() Stats { return g.stats }

// Board 는 굳은 블록 배열(H×W). 호출자는 읽기만 해야 한다.
func (g *Game) Board() *Board { return &g.board }

// Cells 는 보이는 20줄의 굳은 블록. Overlay 는 현재 조각과 고스트.
// 둘을 나눠 두면 화면이 "굳은 것"과 "떨어지는 것"을 다른 색으로 칠하기 쉽다.
func (g *Game) Cells() []uint8   { return g.cells[:] }
func (g *Game) Overlay() []uint8 { return g.overlay[:] }

// Next 는 다음 조각 큐에서 n 개를 미리 본다.
func (g *Game) Next(n int) []int {
	if n > len(g.nextQ) {
		n = len(g.nextQ)
	}
	out := make([]int, n)
	copy(out, g.nextQ[:n])
	return out
}
