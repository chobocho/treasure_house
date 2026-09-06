package ai

import (
	"encoding/json"
	"os"
	"testing"

	"treasure/tetris_tui/core"
)

// parity_test.go — 이 Go AI 가 C++ wasm 의 AI(ai.cpp)와 같은 수를 고르는지 확인한다.
//
// 정답지 test/golden/ai_traces.json 은 2편의 wasm 에서 뽑은 것이다.
// 세 단계로 좁혀 간다 — 평가 → 탐색 → 실전. 앞에서 갈라지면 뒤는 볼 필요가 없다.

const goldenAIPath = "../test/golden/ai_traces.json"

type goldenEval struct {
	B     int       `json:"b"`
	Wi    int       `json:"wi"`
	Score float64   `json:"score"`
	Feat  []float64 `json:"feat"`
}

type goldenPlan struct {
	B      int       `json:"b"`
	P      int       `json:"p"`
	Wi     int       `json:"wi"`
	Packed int       `json:"packed"`
	Feat   []float64 `json:"feat"`
	After  []int64   `json:"after"`
}

type goldenPlay struct {
	Wi        int     `json:"wi"`
	Seed      uint32  `json:"seed"`
	MaxPieces int     `json:"maxPieces"`
	Every     int     `json:"every"`
	R         []int64 `json:"r"`
}

type goldenAIFile struct {
	V          int          `json:"v"`
	WeightSets int          `json:"weightSets"`
	Boards     int          `json:"boards"`
	EvalCases  []goldenEval `json:"evalCases"`
	Plan       []goldenPlan `json:"plan"`
	Play       []goldenPlay `json:"play"`
}

func loadGoldenAI(t *testing.T) *goldenAIFile {
	t.Helper()
	raw, err := os.ReadFile(goldenAIPath)
	if err != nil {
		t.Fatalf("정답지를 못 읽었다: %v", err)
	}
	var g goldenAIFile
	if err := json.Unmarshal(raw, &g); err != nil {
		t.Fatalf("정답지 파싱 실패: %v", err)
	}
	if g.V != 1 {
		t.Fatalf("정답지 버전이 %d 다", g.V)
	}
	return &g
}

func TestGoldenAIFileShape(t *testing.T) {
	g := loadGoldenAI(t)
	if g.WeightSets != len(WeightSets) {
		t.Errorf("정답지의 가중치 묶음이 %d개 — 우리는 %d개다", g.WeightSets, len(WeightSets))
	}
	if boards := len(Boards()); g.Boards != boards {
		t.Errorf("정답지의 판이 %d개 — 우리는 %d개다", g.Boards, boards)
	}
	if len(g.EvalCases) == 0 || len(g.Plan) == 0 || len(g.Play) == 0 {
		t.Fatal("정답지가 비어 있다")
	}
}

// 1) 평가 파리티 — 특징 함수와 내적만 대조한다.
//
// float32 를 double 로 올려 비교하므로 **정확히** 같아야 한다.
// 오차 허용치를 두면 안 된다. 여기서 조금이라도 다르면 탐색의 argmax 가 갈리고,
// "거의 같은 AI"가 아니라 "다른 AI"가 되기 때문이다.
func TestEvalParity(t *testing.T) {
	g := loadGoldenAI(t)
	got := RunEvalTrace(Boards(), 0x4d2)
	if len(got) != len(g.EvalCases) {
		t.Fatalf("평가 경우가 %d개 — 정답은 %d개다", len(got), len(g.EvalCases))
	}
	for i, w := range g.EvalCases {
		c := got[i]
		if c.B != w.B || c.Wi != w.Wi {
			t.Fatalf("%d번 경우의 좌표가 (%d,%d) — 정답은 (%d,%d)다", i, c.B, c.Wi, w.B, w.Wi)
		}
		for k := 0; k < FCount; k++ {
			if float64(c.Feat[k]) != w.Feat[k] {
				t.Fatalf("판%d 가중치%d: %s 가 %v — 정답은 %v다",
					w.B, w.Wi, FeatureNames[k], c.Feat[k], w.Feat[k])
			}
		}
		if float64(c.Score) != w.Score {
			t.Fatalf("판%d 가중치%d: 점수가 %v — 정답은 %v다", w.B, w.Wi, c.Score, w.Score)
		}
	}
}

// 2) 탐색 파리티 — 판 29 × 조각 7 × 가중치 7 = 1421 경우.
// 고른 수(packed)와 그 수의 특징 벡터, 그리고 둔 뒤의 판까지 대조한다.
func TestPlanParity(t *testing.T) {
	g := loadGoldenAI(t)
	got := RunPlanTrace(Boards(), 0x4d2)
	if len(got) != len(g.Plan) {
		t.Fatalf("탐색 경우가 %d개 — 정답은 %d개다", len(got), len(g.Plan))
	}
	bad := 0
	for i, w := range g.Plan {
		c := got[i]
		if c.B != w.B || c.P != w.P || c.Wi != w.Wi {
			t.Fatalf("%d번 경우의 좌표가 (%d,%d,%d) — 정답은 (%d,%d,%d)다",
				i, c.B, c.P, c.Wi, w.B, w.P, w.Wi)
		}
		if c.Packed != w.Packed {
			if bad < 5 {
				t.Errorf("판%d %s 가중치%d: 고른 수가 %d — 정답은 %d다%s",
					w.B, core.PieceNames[w.P], w.Wi, c.Packed, w.Packed,
					describeMoves(c.Packed, w.Packed))
			}
			bad++
			continue
		}
		// 둘 수 없는 경우(-1)에는 특징 벡터가 갱신되지 않는다 — 대조 대상이 아니다.
		if w.Packed >= 0 {
			for k := 0; k < FCount; k++ {
				if float64(c.Feat[k]) != w.Feat[k] {
					if bad < 5 {
						t.Errorf("판%d %s 가중치%d: %s 가 %v — 정답은 %v다",
							w.B, core.PieceNames[w.P], w.Wi, FeatureNames[k], c.Feat[k], w.Feat[k])
					}
					bad++
					break
				}
			}
		}
		mine := []int64{int64(c.Hash), int64(c.After[0]), int64(c.After[1]), int64(c.After[2]), int64(c.After[3])}
		for k := range w.After {
			if mine[k] != w.After[k] {
				if bad < 5 {
					t.Errorf("판%d %s 가중치%d: 둔 뒤 %s 가 %d — 정답은 %d다",
						w.B, core.PieceNames[w.P], w.Wi, planAfterNames[k], mine[k], w.After[k])
				}
				bad++
				break
			}
		}
	}
	if bad > 0 {
		t.Errorf("탐색 경우 %d개 중 %d개가 어긋났다", len(got), bad)
	}
}

var planAfterNames = [5]string{"보드해시", "점수", "누적줄", "상태", "공격"}

// describeMoves 는 접힌 수를 사람이 읽을 수 있게 푼다. 실패 메시지에서만 쓴다.
func describeMoves(got, want int) string {
	s := ""
	if m, ok := Unpack(got); ok {
		s += " (고른 수: 홀드=" + boolStr(m.UseHold) + " rot=" + itoa(m.Rot) + " x=" + itoa(m.X)
	} else {
		s += " (고른 수: 없음"
	}
	if m, ok := Unpack(want); ok {
		s += " / 정답: 홀드=" + boolStr(m.UseHold) + " rot=" + itoa(m.Rot) + " x=" + itoa(m.X) + ")"
	} else {
		s += " / 정답: 없음)"
	}
	return s
}

func boolStr(b bool) string {
	if b {
		return "예"
	}
	return "아니오"
}

func itoa(n int) string {
	if n == 0 {
		return "0"
	}
	neg := n < 0
	if neg {
		n = -n
	}
	var b []byte
	for n > 0 {
		b = append([]byte{byte('0' + n%10)}, b...)
		n /= 10
	}
	if neg {
		return "-" + string(b)
	}
	return string(b)
}

// 3) 실전 파리티 — 가중치 7 × 시드 4 × 가비지 2가지 = 56판, 각 400조각.
// 여기까지 맞으면 "우연히 맞은" 가능성이 사실상 없다.
func TestPlayParity(t *testing.T) {
	g := loadGoldenAI(t)
	if len(g.Play) == 0 {
		t.Fatal("실전 정답지가 비어 있다")
	}
	maxPieces := g.Play[0].MaxPieces
	got := RunPlayTrace(maxPieces)
	if len(got) != len(g.Play) {
		t.Fatalf("실전 판이 %d개 — 정답은 %d개다", len(got), len(g.Play))
	}
	for i, w := range g.Play {
		c := got[i]
		if c.Wi != w.Wi || c.Seed != w.Seed || c.Every != w.Every {
			t.Fatalf("%d번 판의 설정이 (%d,%d,%d) — 정답은 (%d,%d,%d)다",
				i, c.Wi, c.Seed, c.Every, w.Wi, w.Seed, w.Every)
		}
		mine := []int64{
			int64(c.R[0]), int64(c.R[1]), int64(c.R[2]),
			int64(c.R[3]), int64(c.R[4]), int64(c.R[5]), int64(c.Hash),
		}
		for k := range w.R {
			if mine[k] != w.R[k] {
				t.Errorf("가중치%d 시드%d every=%d: %s 가 %d — 정답은 %d다",
					w.Wi, w.Seed, w.Every, playFieldNames[k], mine[k], w.R[k])
				break
			}
		}
	}
}

var playFieldNames = [7]string{"지운줄", "공격", "놓은조각", "점수", "레벨", "상태", "보드해시"}

// 정답지가 흥미로운 경우를 실제로 담고 있는지 본다.
// "둘 수 없음"과 "홀드 사용"이 한 번도 안 나오면 그 분기는 검증된 적이 없는 것이다.
func TestPlanTraceCoversInterestingBranches(t *testing.T) {
	cases := RunPlanTrace(Boards(), 0x4d2)
	var noMove, usedHold int
	for _, c := range cases {
		if c.Packed < 0 {
			noMove++
			continue
		}
		if m, _ := Unpack(c.Packed); m.UseHold {
			usedHold++
		}
	}
	t.Logf("탐색 트레이스 %d경우 — 둘 수 없음 %d, 홀드 사용 %d", len(cases), noMove, usedHold)
	if noMove == 0 {
		t.Error("'둘 수 없음' 경로를 한 번도 안 밟았다")
	}
	if usedHold == 0 {
		t.Error("홀드를 한 번도 안 썼다")
	}
}
