package ai

import "treasure/tetris_tui/core"

// trace.go — AI 파리티용 시나리오 생성기.
//
// core/trace.go 와 같은 구조다: 시나리오를 한 곳에만 두고, C++ wasm 과 Go 가
// 같은 길을 걷게 한 뒤 도착지를 비교한다.
//
// AI 파리티는 코어 파리티보다 까다롭다. 평가 점수가 float32 라
// **마지막 비트 하나만 달라도 argmax 가 다른 후보를 고르고**, 그때부터 판이
// 통째로 갈라지기 때문이다. 그래서 세 단계로 좁혀 간다:
//
//	평가(EvalHere)   → 특징 함수만 대조. 갈라지면 특징이 틀린 것이다.
//	탐색(Best)       → 고른 수를 판마다 대조. 갈라지면 탐색·동점 처리가 틀린 것이다.
//	실전(Play)       → 400조각을 통째로 돌려 누적 결과까지 대조.

// WeightSets 는 대조에 쓰는 가중치 묶음.
//
// 앞의 넷은 2편의 GA 가 실제로 뽑아 낸 난이도별 가중치다(weights.json).
// 뒤의 셋은 손으로 만든 극단값 — 전부 0, 전부 양수, 2의 거듭제곱.
// 극단값이 중요하다: 부호가 뒤집히면 AI 가 일부러 판을 높이 쌓아서
// "블록아웃 직전"과 "둘 수 있는 수가 없음" 경로를 밟는다.
var WeightSets = []Weights{
	{0.07328, 0.064795, -0.477997, 0.210324, -0.008971, -0.391833, -0.504655, -0.556259}, // max
	{-0.3458, -0.1764, -0.7118, 0.2672, -0.3872, -0.1953, -0.2603, -0.1243},              // normal
	{-0.0367, -0.5056, 0.4788, -0.0219, -0.4999, -0.4376, -0.195, -0.184},                // easy
	{-0.031, 0.0583, -0.6088, 0.2292, -0.1135, -0.378, -0.3072, -0.5678},                 // hard
	{0, 0, 0, 0, 0, 0, 0, 0}, // 전부 0 — 첫 후보가 그대로 최선(동점 처리 확인)
	{1, 1, 1, 1, 1, 1, 1, 1}, // 전부 양수 — 최악의 수를 고른다
	{0.5, -0.25, 0.125, -0.0625, 0.03125, -0.015625, 0.0078125, -0.00390625}, // 2의 거듭제곱
}

// PlaySeeds 는 실전 대조에 쓰는 시드.
var PlaySeeds = []uint32{1, 2, 3, 777}

// BoardCount 는 무작위 판의 개수. 도구와 테스트가 같은 수를 써야 하므로 여기서 고정한다.
const BoardCount = 24

// RandomBoards 는 대조용 무작위 판을 만든다.
//
// 열마다 높이를 뽑고, 그 아래를 7칸에 1칸꼴로 비워 구멍을 낸다.
// 구멍이 있어야 F_HOLES·F_COLT·F_WELLS 가 0 이 아닌 값을 갖는다 —
// 평평한 판만 쓰면 특징 8개 중 절반이 늘 0 이라 대조가 헐거워진다.
// 높이 상한은 14 로 잡았다. 더 높이면 스폰이 막혀 대부분의 판이 "둘 수 없음"으로 끝난다.
//
// 주의: `depth <= h[x] && r()%7 != 0` 의 **단축 평가**까지 원본과 같아야 한다.
// 앞이 거짓이면 r() 이 안 불리므로, 난수 소비 횟수가 판의 높이에 따라 달라진다.
func RandomBoards(count int, seed uint32) [][]string {
	r := core.ScriptRng(seed)
	out := make([][]string, 0, count)
	for i := 0; i < count; i++ {
		var h [core.W]int
		for x := 0; x < core.W; x++ {
			h[x] = int(r() % 15)
		}
		rows := make([]string, 0, core.Vis)
		for y := 0; y < core.Vis; y++ {
			buf := make([]byte, core.W)
			depth := core.Vis - y // 바닥에서 센 높이 (바닥줄 = 1)
			for x := 0; x < core.W; x++ {
				buf[x] = '.'
				if depth <= h[x] && r()%7 != 0 {
					buf[x] = '#'
				}
			}
			rows = append(rows, string(buf))
		}
		out = append(out, rows)
	}
	return out
}

// ExtraBoards 는 무작위 판이 절대 만들어 주지 않는 경계 판들.
//
// 특히 "스폰이 막힌 판"이 중요하다. 무작위 판 24개에서는 Best 가 "둘 수 없음"을
// 돌려주는 경우가 한 번도 안 나왔다. 아무도 안 밟는 분기는 검증된 적이 없는 분기다.
var ExtraBoards = [][]string{
	{},                       // 빈 판 — 모든 후보가 유효, F_HOLES 등이 0
	repRow("#########.", 20), // 스폰까지 꽉 참 → SetPiece 가 곧장 게임오버
	repRow("#########.", 16), // 거의 다 참 — 후보가 몇 개 안 남는다
	append([]string{"..........", ".........."}, repRow(".........#", 18)...), // 오른쪽 벽만 높은 판
	repRow(".....#####", 19), // 절반만 높은 판 — 도달 불가 자리가 많이 생긴다
}

func repRow(row string, n int) []string {
	out := make([]string, n)
	for i := range out {
		out[i] = row
	}
	return out
}

// Boards 는 대조에 쓰는 판 전체 = 무작위 + 경계.
func Boards() [][]string {
	return append(RandomBoards(BoardCount, 0x7f4a7c15), ExtraBoards...)
}

// EvalCase 는 특징 함수만 따로 대조한 결과.
// 탐색을 거치지 않으므로, 갈라졌을 때 "특징이 틀렸나 탐색이 틀렸나"를 가른다.
type EvalCase struct {
	B, Wi int
	Score float32
	Feat  [FCount]float32
}

// RunEvalTrace 는 판만 심고 그대로 평가한다.
func RunEvalTrace(boards [][]string, seed uint32) []EvalCase {
	out := make([]EvalCase, 0, len(boards)*len(WeightSets))
	g := &core.Game{}
	for b := range boards {
		for wi, w := range WeightSets {
			g.Init(seed)
			g.Paint(boards[b])
			score, f := EvalHere(g, w)
			out = append(out, EvalCase{B: b, Wi: wi, Score: score, Feat: f})
		}
	}
	return out
}

// PlanCase 는 "이 판에서 AI 가 무엇을 고르는가"의 결과.
type PlanCase struct {
	B, P, Wi int
	Packed   int // -1 이면 둘 수 없음
	Feat     [FCount]float32
	Hash     uint32
	// [점수, 누적줄, 상태, 공격]
	After [4]int32
}

// RunPlanTrace 는 판을 심고 조각을 지정한 뒤 고른 수를 전수로 대조한다.
func RunPlanTrace(boards [][]string, seed uint32) []PlanCase {
	out := make([]PlanCase, 0, len(boards)*core.PieceCount*len(WeightSets))
	g := &core.Game{}
	var s Searcher
	for b := range boards {
		for p := 0; p < core.PieceCount; p++ {
			for wi, w := range WeightSets {
				g.Init(seed)
				g.Paint(boards[b])
				g.SetPiece(p)

				m, f, ok := s.Best(g, w)
				packed := -1
				if ok {
					packed = m.Pack()
					Apply(g, m)
				}
				st := g.Stats()
				out = append(out, PlanCase{
					B: b, P: p, Wi: wi, Packed: packed, Feat: f,
					Hash:  core.BoardHash(g.Board()),
					After: [4]int32{st.Score, st.Lines, st.State, st.Attack},
				})
			}
		}
	}
	return out
}

// PlayCase 는 실전 한 판의 누적 결과.
type PlayCase struct {
	Wi        int
	Seed      uint32
	MaxPieces int
	Every     int
	Hash      uint32
	// [지운줄, 공격, 놓은조각, 점수, 레벨, 상태]
	R [6]int32
}

// RunPlayTrace 는 400조각을 끝까지 둔 뒤의 누적 결과를 대조한다.
//
// every > 0 은 "비가 새는 배" 모드다. 2편의 GA 적합도 함수가 실제로 쓰는 설정이라
// 여기서 맞춰 두지 않으면 학습 결과가 두 구현에서 갈린다.
func RunPlayTrace(maxPieces int) []PlayCase {
	out := make([]PlayCase, 0, len(WeightSets)*len(PlaySeeds)*2)
	for wi, w := range WeightSets {
		for _, seed := range PlaySeeds {
			for _, every := range []int{0, 12} {
				r := Play(w, seed, maxPieces, every)
				st := r.Game.Stats()
				out = append(out, PlayCase{
					Wi: wi, Seed: seed, MaxPieces: maxPieces, Every: every,
					Hash: core.BoardHash(r.Game.Board()),
					R: [6]int32{
						int32(r.Lines), int32(r.Attack), int32(r.Placed),
						st.Score, st.Level, st.State,
					},
				})
			}
		}
	}
	return out
}
