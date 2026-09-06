package core

// trace.go — "이 Go 코어가 C++ 코어와 정말 같은가"를 재는 자.
//
// 이 파일은 게임을 하지 않는다. **시나리오를 만든다.** 어떤 키를 언제 누르고
// dt 를 얼마나 흘릴지를 정하고, 그걸 그대로 코어에 먹인 뒤 매 스텝의 해시를 남긴다.
// 같은 시나리오를 C++ wasm 코어에 먹여 뽑아 둔 정답지가 test/golden/core_traces.json 이고,
// parity_test.go 가 둘을 한 스텝씩 맞춰 본다.
//
// 시나리오 생성기를 여기 두는 이유. 두 구현이 각자 시나리오를 만들면
// 서로 다른 길을 걸어 놓고 "도착지가 다르네" 하고 헤매게 된다. 길은 하나여야 한다.
// (TS 판인 tetris_ts/src/trace.ts 와 같은 구조이고, 상수도 같은 값을 쓴다)
//
// 트레이스는 세 종류다:
//
//  1. 플레이 트레이스 — 조각 단위 계획으로 실제 게임을 1500스텝씩 돌린다.
//     무작위 키 난타는 8조각 만에 죽어서 줄 지우기·콤보·B2B 를 한 번도 못 밟는다.
//  2. 배치 트레이스 — 판을 심어 놓고 짧은 입력 단어를 전수로 넣는다.
//     SRS 킥의 구석과 T스핀 판정처럼 "우연히 걸리기를 기다릴 수 없는" 것들을 겨냥한다.
//  3. 연쇄 트레이스 — 판을 다시 심어 가며 클리어를 이어 붙인다.
//     콤보 누적·B2B·레벨업·가비지 상쇄는 여러 번의 클리어가 이어져야만 드러난다.

// 트레이스에 쓰는 시드들. 뒤의 둘은 경계값 — 0 은 코어가 기본 시드로 바꿔야 하고,
// 0xFFFFFFFF 는 xorshift 의 u32 경계를 밟는다.
var TraceSeeds = []uint32{1, 2, 12345, 0x9e3779b9, 0, 0xffffffff}

const (
	TraceSteps = 1500
	// 이 간격마다 stats 전체를 스냅샷으로 남긴다 — 해시가 어긋났을 때 어디가 다른지 보려고.
	SnapEvery = 100
)

// ScriptRng 는 시나리오 생성용 난수.
//
// 게임 RNG(Rng)와 **다른** 수열이어야 한다. 같은 수열을 쓰면 "RNG 가 틀렸는데
// 시나리오도 같이 틀려서 결과가 맞아 보이는" 상황이 생긴다.
// 그래서 시드를 한 번 비틀고, 시프트 값도 다른 조합(7/9/8)을 쓴다.
func ScriptRng(seed uint32) func() uint32 {
	s := seed ^ 0x5bf03635
	if s == 0 {
		s = 0x1234567
	}
	return func() uint32 {
		s ^= s << 7
		s ^= s >> 9
		s ^= s << 8
		return s
	}
}

// LowestColumn 은 판에서 가장 낮은 열(동률이면 왼쪽)의 x.
// 판 배열만 보고 정하므로 두 구현이 같은 판 위에서 반드시 같은 답을 낸다.
func LowestColumn(b *Board) int {
	best, bestH := 0, H+1
	for x := 0; x < W; x++ {
		y := 0
		for y < H && b[y*W+x] == 0 {
			y++
		}
		if h := H - y; h < bestH {
			bestH, best = h, x
		}
	}
	return best
}

// TraceStep 은 한 스텝에 일어나는 일. Act/Rel 의 -1 은 "아무것도 안 함".
type TraceStep struct {
	Act, Rel int
	DtMs     int
	Garbage  int
}

// PlanPiece 는 조각 하나를 어떻게 둘지에 대한 계획을 스텝 목록으로 펼친다.
//
//	(가끔) 홀드 → 회전 0~3회 → 목표 열까지 이동 → (가끔) DAS·소프트드롭 →
//	하드드롭 또는 자연 낙하 → 잠깐 쉼
//
// 목표 열은 호출자가 **현재 판을 보고** 정해서 넘긴다. 무작위로 고르면 조각이
// 한곳에 쌓여 17조각 만에 죽고, 그러면 줄 지우기·콤보·B2B·레벨업이 트레이스에
// 한 번도 안 들어온다. 낮은 열로 보내면 판이 평평해져서 줄이 지워지고 게임이 길어진다.
func PlanPiece(r func() uint32, targetX int) []TraceStep {
	var out []TraceStep
	push := func(act, rel, dtMs, garbage int) {
		out = append(out, TraceStep{Act: act, Rel: rel, DtMs: dtMs, Garbage: garbage})
	}

	if r()%9 == 0 {
		push(int(ActHold), -1, 2, 0)
	}

	rots := r() % 4
	for k := uint32(0); k < rots; k++ {
		act := int(ActCW)
		if r()%5 == 0 {
			act = int(ActCCW)
		}
		push(act, -1, 2, 0)
	}
	if r()%13 == 0 {
		push(int(ActFlip), -1, 2, 0)
	}

	// 스폰 x 는 3. 목표 열에 조각의 왼쪽 끝을 맞춘다 (벽에 막히면 코어가 알아서 멈춘다).
	dx := targetX - 1 - SpawnX
	dir := int(ActRight)
	if dx < 0 {
		dir = int(ActLeft)
	}
	n := dx
	if n < 0 {
		n = -n
	}
	for k := 0; k < n; k++ {
		push(dir, dir, 3, 0) // 눌렀다 떼기 — DAS 폭주 방지
	}

	// 가끔은 DAS 를 진짜로 돌린다: 누른 채로 200ms 를 흘린 뒤 뗀다
	if r()%9 == 0 {
		push(dir, -1, 100, 0)
		push(-1, -1, 100, 0)
		push(-1, dir, 60, 0)
	}
	// 가끔은 소프트드롭으로 가라앉힌다 — 회전 뒤에 가라앉히면 스핀이 나온다
	if r()%5 == 0 {
		push(int(ActSoft), -1, 100, 0)
		push(-1, int(ActSoft), 20, 0)
	}

	if r()%11 == 0 {
		// 자연 낙하 + 락다운 유예 경로. 하드드롭만 쓰면 이 코드가 트레이스에 안 들어온다.
		for k := 0; k < 12; k++ {
			push(-1, -1, 100, 0)
		}
	} else {
		push(int(ActHard), -1, 5, 0)
	}

	// 가비지는 드물게. 자주 넣으면 판이 금방 천장에 닿아 게임이 짧아진다.
	garb := 0
	if r()%45 == 0 {
		garb = 1 + int(r()%4)
	}
	push(-1, -1, 1+int(r()%30), garb)
	return out
}

// Snap 은 스냅샷 한 장 — 스텝 번호와 그때의 stats 전체.
type Snap struct {
	I     int
	Stats [StatCount]int32
}

// TraceResult 는 시드 하나의 트레이스 결과.
type TraceResult struct {
	Seed     uint32
	Steps    int
	BH       []uint32 // 스텝마다의 보드 해시
	SH       []uint32 // 스텝마다의 stats 해시
	Snaps    []Snap
	Restarts int // 진행 중 게임오버로 재시작한 횟수
}

// RunTrace 는 시나리오를 끝까지 돌리고 스텝마다 해시를 남긴다.
//
// 게임오버가 나면 그 자리에서 파생 시드로 재시작한다. 그러지 않으면 트레이스의
// 뒷부분이 전부 "아무 일도 안 일어남"이 되어 검증력이 사라진다.
// 재시작 시드는 원래 시드와 스텝 번호만으로 정해지므로 두 구현이 반드시 같은
// 지점에서 같은 시드로 다시 시작한다.
func RunTrace(g *Game, seed uint32, steps int) TraceResult {
	r := ScriptRng(seed)
	g.Init(seed)
	res := TraceResult{Seed: seed, Steps: steps}
	var queue []TraceStep

	for i := 0; i < steps; i++ {
		// 계획이 떨어지면 지금 판을 보고 새로 세운다. 시나리오가 판에 반응하므로,
		// 어느 한쪽이 판을 다르게 만들면 그다음 입력까지 갈라져서 차이가 증폭된다.
		if len(queue) == 0 {
			queue = PlanPiece(r, LowestColumn(g.Board()))
		}
		st := queue[0]
		queue = queue[1:]

		if st.Garbage > 0 {
			g.QueueGarbage(st.Garbage)
		}
		if st.Act >= 0 {
			g.Press(Action(st.Act))
		}
		if st.Rel >= 0 {
			g.Release(Action(st.Rel))
		}
		g.Update(st.DtMs)

		if g.Stats().State == StateOver {
			res.Restarts++
			g.Init((seed + uint32(i)*2654435761) ^ 0x85ebca6b)
			queue = nil // 새 판에는 새 계획
		}

		res.BH = append(res.BH, BoardHash(g.Board()))
		res.SH = append(res.SH, StatsHash(g.Stats()))
		if i%SnapEvery == 0 || i == steps-1 {
			res.Snaps = append(res.Snaps, Snap{I: i, Stats: g.Stats().Pack()})
		}
	}
	return res
}

// ── 2부: 배치 트레이스 (킥·T스핀·점수의 정면 대조) ────────────────────

func repRow(row string, n int) []string {
	out := make([]string, n)
	for i := range out {
		out[i] = row
	}
	return out
}

// TraceBoards 는 배치 트레이스에 쓰는 판 5종. 각각 다른 종류의 함정을 담고 있다.
//
// 1번 판이 이 트레이스의 핵심이다. T스핀 더블 자리를 **스폰 높이 근처**에 만들어 뒀다.
// 바닥에 만들면 조각이 15칸을 내려가야 하는데, 그동안 락다운 타이머가 돌아
// "회전할 기회"가 사라진다. 함정을 위로 올려야 스핀이 실제로 성립한다.
var TraceBoards = [][]string{
	// 0) 빈 판 — 스폰·기본 회전·바닥 킥
	{},
	// 1) T스핀 더블 자리: 오버행 2개(x=2,5) + 3칸 방 + 1칸 노치(x=4)
	append([]string{"..#..#....", "###...####", "####.#####"}, repRow("#########.", 15)...),
	// 2) 계단 — 벽킥과 끼워넣기가 많이 나온다
	{
		"#.........", "##........", "###.......", "####......",
		"#####.....", "######....", "#######...", "########..",
	},
	// 3) 이미 꽉 찬 줄이 섞인 판 — 락 순간의 줄 지우기 경로
	append([]string{"##########"}, repRow("#########.", 4)...),
	// 4) 왼쪽 1칸 우물 — I 를 세워 꽂으면 테트리스, B2B 가 붙는다
	repRow(".#########", 12),
}

// PlaceOp 은 배치 트레이스의 연산 하나: 키를 누르거나(Press ≥ 0) 시간을 흘리거나(Wait > 0).
type PlaceOp struct {
	Press int
	Wait  int
}

func opPress(a Action) PlaceOp { return PlaceOp{Press: int(a), Wait: -1} }
func opWait(ms int) PlaceOp    { return PlaceOp{Press: -1, Wait: ms} }

// SpinWords 는 손으로 짠 "스핀 단어" — 소프트드롭으로 가라앉힌 뒤 회전해서 킥으로 밀어 넣는다.
//
// 왜 손으로 짜는가: 무작위 단어 48개로는 T스핀이 한 번도 안 나온다(실제로 0회였다).
// T스핀은 "가라앉힌 다음 회전"이라는 순서가 반드시 필요한데,
// 무작위 단어에는 시간을 흘리는 연산 자체가 없기 때문이다.
//
// 1번 판 + T조각 + 첫 단어가 정식 T스핀 더블이 되도록 킥 표를 따라가며 맞췄다:
// CW(rot1) → LEFT → 소프트드롭 1칸 → CW 에서 k=0,1 이 막히고 k=2 {+1,-1} 이
// 조각을 오른쪽 아래로 밀어 노치에 앉힌다 → 앞 코너 2개 + 뒤 1개 = 정식.
var SpinWords = [][]PlaceOp{
	{opPress(ActCW), opPress(ActLeft), opPress(ActSoft), opWait(100), opPress(ActCW), opPress(ActHard)},
	{opPress(ActCCW), opPress(ActRight), opPress(ActSoft), opWait(100), opPress(ActCCW), opPress(ActHard)},
	{opPress(ActSoft), opWait(100), opWait(100), opPress(ActCW), opPress(ActHard)},
	{opPress(ActCW), opPress(ActCW), opPress(ActSoft), opWait(100), opPress(ActCCW), opPress(ActHard)},
	{opPress(ActLeft), opPress(ActSoft), opWait(100), opPress(ActCW), opPress(ActCW), opPress(ActHard)},
	{opPress(ActRight), opPress(ActCW), opPress(ActSoft), opWait(100), opPress(ActFlip), opPress(ActHard)},
	// 하드드롭 없이 락다운 유예로 굳는 경로 (500ms)
	{opPress(ActCW), opPress(ActSoft), opWait(100), opWait(100), opWait(100), opWait(100), opWait(100), opWait(100)},
	// 홀드로 조각을 바꿔치기한 뒤 두는 경로
	{opPress(ActHold), opPress(ActCW), opPress(ActLeft), opPress(ActHard)},
}

// RandomWords 는 무작위 입력 단어 — 하드드롭으로 끝나는 짧은 키 시퀀스.
func RandomWords(count int) [][]PlaceOp {
	r := ScriptRng(0x1d872b41)
	keys := []Action{ActLeft, ActRight, ActCW, ActCCW, ActFlip, ActSoft, ActHold}
	out := make([][]PlaceOp, 0, count)
	for i := 0; i < count; i++ {
		n := 1 + int(r()%6)
		w := make([]PlaceOp, 0, n+1)
		for k := 0; k < n; k++ {
			w = append(w, opPress(keys[int(r())%len(keys)]))
		}
		w = append(w, opPress(ActHard)) // 반드시 굳혀서 결과가 보드에 남게 한다
		out = append(out, w)
	}
	return out
}

// InputWords 는 배치 트레이스가 쓰는 단어 전체 = 손으로 짠 것 + 무작위.
func InputWords() [][]PlaceOp {
	return append(append([][]PlaceOp{}, SpinWords...), RandomWords(48)...)
}

// PlacementCase 하나 = (판, 조각, 단어) 조합 하나의 결과.
//
// 해시를 stats 와 따로 두는 이유: 보드 해시는 부호 없는 32비트라 int32 에 안 들어간다.
// 정답지 JSON 에서도 42억까지 올라가는 수로 적혀 있다.
type PlacementCase struct {
	B, P, Wd int
	Hash     uint32
	// [점수, 지운줄, T스핀, 상태, 공격, 누적줄, B2B]
	R [7]int32
}

// RunPlacementTrace 는 배치 트레이스를 전수로 돌린다. 판 5 × 조각 7 × 단어 56 = 1960 경우.
func RunPlacementTrace(g *Game, seed uint32) []PlacementCase {
	words := InputWords()
	out := make([]PlacementCase, 0, len(TraceBoards)*PieceCount*len(words))
	for b := range TraceBoards {
		for p := 0; p < PieceCount; p++ {
			for w := range words {
				g.Init(seed)
				g.Paint(TraceBoards[b])
				g.SetPiece(p)
				for _, op := range words[w] {
					if op.Press >= 0 {
						g.Press(Action(op.Press))
					} else {
						g.Update(op.Wait)
					}
				}
				s := g.Stats()
				out = append(out, PlacementCase{B: b, P: p, Wd: w,
					Hash: BoardHash(g.Board()),
					R:    [7]int32{s.Score, s.Clear, s.TSpin, s.State, s.Attack, s.Lines, s.B2B},
				})
			}
		}
	}
	return out
}

// ── 3부: 연쇄 트레이스 (콤보 · B2B · 레벨업 · 상쇄) ────────────────────
//
// 배치 트레이스는 경우마다 Init() 하므로 락이 딱 한 번씩만 일어난다.
// 그래서 **여러 번의 클리어가 이어져야 드러나는 규칙**을 하나도 못 밟는다:
// 콤보 누적, Back-to-Back ×1.5, 10줄마다 레벨업, 대기 가비지의 상쇄와 솟아오름.
// 여기서는 인스턴스를 유지한 채 판만 다시 심어서 그 연쇄를 강제로 만든다.
// 판을 다시 심어도 콤보·B2B·레벨은 stats 에 남아 있으므로 연쇄가 끊기지 않는다.

// ComboRound 하나: 판을 심고 → 조각을 지정하고 → (가비지 예약) → 입력 단어를 넣는다.
type ComboRound struct {
	Board   []string
	Piece   int
	Word    []PlaceOp
	Garbage int
}

type ComboScenario struct {
	Name   string
	Rounds []ComboRound
}

var (
	tetrisWell = append(repRow(".#########", 4), "#########.")
	singleWell = []string{".#########", "#########."}
	noClear    = []string{"#########."}

	// I 를 세워서 왼쪽 끝 우물에 꽂는다. 벽에 막히면 코어가 알아서 멈추므로 6번이면 충분하다.
	wordILeft = []PlaceOp{
		opPress(ActCW),
		opPress(ActLeft), opPress(ActLeft), opPress(ActLeft),
		opPress(ActLeft), opPress(ActLeft), opPress(ActLeft),
		opPress(ActHard),
	}
	// 그냥 떨어뜨린다 — 줄이 안 지워지는 락(콤보 끊김 · 가비지 솟아오름)을 만든다.
	wordDrop = []PlaceOp{opPress(ActHard)}
)

// ComboScenarios 는 연쇄 규칙을 하나씩 겨냥한 시나리오 넷.
func ComboScenarios() []ComboScenario {
	var out []ComboScenario

	// 테트리스만 8연속 → B2B 가 계속 붙고(×1.5), 콤보가 0→7 로 자라고, 32줄에 레벨 4
	var s0 []ComboRound
	for i := 0; i < 8; i++ {
		s0 = append(s0, ComboRound{Board: tetrisWell, Piece: PieceI, Word: wordILeft})
	}
	out = append(out, ComboScenario{Name: "테트리스 8연속", Rounds: s0})

	// 테트리스와 싱글을 번갈아 → 싱글에서 B2B 가 끊기고 다음 테트리스에서 다시 붙는다
	var s1 []ComboRound
	for i := 0; i < 10; i++ {
		b := tetrisWell
		if i%2 != 0 {
			b = singleWell
		}
		s1 = append(s1, ComboRound{Board: b, Piece: PieceI, Word: wordILeft})
	}
	out = append(out, ComboScenario{Name: "테트리스와 싱글 교차", Rounds: s1})

	// T스핀 더블 6연속 → T스핀도 "어려운 클리어"라 B2B 가 붙는다
	var s2 []ComboRound
	for i := 0; i < 6; i++ {
		s2 = append(s2, ComboRound{Board: TraceBoards[1], Piece: PieceT, Word: SpinWords[0]})
	}
	out = append(out, ComboScenario{Name: "T스핀 더블 6연속", Rounds: s2})

	// 지우기와 못 지우기를 번갈아 → 콤보가 매번 끊기고, 예약한 가비지가 실제로 솟는다
	var s3 []ComboRound
	for i := 0; i < 12; i++ {
		if i%2 == 0 {
			s3 = append(s3, ComboRound{Board: singleWell, Piece: PieceI, Word: wordILeft, Garbage: 3})
		} else {
			s3 = append(s3, ComboRound{Board: noClear, Piece: PieceO, Word: wordDrop})
		}
	}
	out = append(out, ComboScenario{Name: "콤보 끊기와 가비지 솟아오름", Rounds: s3})

	return out
}

// ComboStep 하나 = 한 라운드의 결과.
type ComboStep struct {
	S, I int
	Hash uint32
	// [점수, 이번획득, 지운줄, T스핀, 콤보, B2B, 레벨, 누적줄, 공격, 대기, 퍼펙트]
	R [11]int32
}

// RunComboTrace 는 연쇄 시나리오를 전부 돌린다.
func RunComboTrace(g *Game, seed uint32) []ComboStep {
	var out []ComboStep
	scenarios := ComboScenarios()
	for si, sc := range scenarios {
		g.Init(seed)
		for i, rd := range sc.Rounds {
			g.Paint(rd.Board)
			if rd.Garbage > 0 {
				g.QueueGarbage(rd.Garbage)
			}
			g.SetPiece(rd.Piece)
			for _, op := range rd.Word {
				if op.Press >= 0 {
					g.Press(Action(op.Press))
				} else {
					g.Update(op.Wait)
				}
			}
			s := g.Stats()
			out = append(out, ComboStep{S: si, I: i,
				Hash: BoardHash(g.Board()),
				R: [11]int32{
					s.Score, s.Gain, s.Clear, s.TSpin, s.Combo, s.B2B,
					s.Level, s.Lines, s.Attack, s.Pending, s.Perfect,
				},
			})
		}
	}
	return out
}
