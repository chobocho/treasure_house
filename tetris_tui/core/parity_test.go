package core

import (
	"encoding/json"
	"os"
	"testing"
)

// parity_test.go — 이 Go 코어가 C++ wasm 코어와 **한 스텝씩** 같은지 확인한다.
//
// 정답지 test/golden/core_traces.json 은 이 저장소의 1편(tetris_ai/tetris_ai.wasm)에서
// 뽑은 것이다. 우리는 그 파일을 만들지 않았고 고치지도 않았다 — 그래서 이 테스트가
// 통과하면 "규칙을 옳게 이식했다"가 아니라 "규칙이 원본과 같다"를 말할 수 있다.
//
// 이 파일 하나가 core 패키지의 나머지 테스트 전부보다 검증력이 세다.
// 단위 테스트는 내가 생각한 경우만 보지만, 여기서는 9000스텝과 1960가지 배치가
// 전부 원본과 대조된다.

const goldenCorePath = "../test/golden/core_traces.json"

type goldenSnap struct {
	I     int     `json:"i"`
	Stats []int32 `json:"stats"`
}

type goldenTrace struct {
	Seed     uint32       `json:"seed"`
	Steps    int          `json:"steps"`
	BH       []uint32     `json:"bh"`
	SH       []uint32     `json:"sh"`
	Snaps    []goldenSnap `json:"snaps"`
	Restarts int          `json:"restarts"`
}

type goldenPlacement struct {
	B  int     `json:"b"`
	P  int     `json:"p"`
	Wd int     `json:"w"`
	R  []int64 `json:"r"`
}

type goldenCombo struct {
	S int     `json:"s"`
	I int     `json:"i"`
	R []int64 `json:"r"`
}

type goldenFile struct {
	V         int               `json:"v"`
	Note      string            `json:"note"`
	Source    string            `json:"source"`
	Steps     int               `json:"steps"`
	Traces    []goldenTrace     `json:"traces"`
	Placement []goldenPlacement `json:"placement"`
	Combo     []goldenCombo     `json:"combo"`
}

func loadGolden(t *testing.T) *goldenFile {
	t.Helper()
	raw, err := os.ReadFile(goldenCorePath)
	if err != nil {
		t.Fatalf("정답지를 못 읽었다: %v", err)
	}
	var g goldenFile
	if err := json.Unmarshal(raw, &g); err != nil {
		t.Fatalf("정답지 파싱 실패: %v", err)
	}
	if g.V != 1 {
		t.Fatalf("정답지 버전이 %d 다", g.V)
	}
	return &g
}

// 정답지가 우리가 아는 그 파일인지 먼저 확인한다.
// 시드 목록이나 스텝 수가 바뀌었으면 아래 테스트들이 엉뚱한 걸 대조하게 된다.
func TestGoldenFileShape(t *testing.T) {
	g := loadGolden(t)
	if g.Steps != TraceSteps {
		t.Errorf("정답지의 스텝 수가 %d — 우리 상수는 %d 다", g.Steps, TraceSteps)
	}
	if len(g.Traces) != len(TraceSeeds) {
		t.Fatalf("정답지에 트레이스가 %d개 — 시드는 %d개다", len(g.Traces), len(TraceSeeds))
	}
	for i, tr := range g.Traces {
		if tr.Seed != TraceSeeds[i] {
			t.Errorf("%d번 시드가 %d — %d 를 기대했다", i, tr.Seed, TraceSeeds[i])
		}
	}
	if len(g.Placement) == 0 || len(g.Combo) == 0 {
		t.Error("배치·연쇄 트레이스가 비어 있다")
	}
}

// 1) 플레이 트레이스 — 시드 6개 × 1500스텝. 매 스텝의 보드 해시와 stats 해시를 맞춘다.
//
// 어긋나면 첫 어긋난 스텝에서 바로 멈춘다. 그 뒤는 전부 파생 오류라 읽을 가치가 없다.
// 대신 그 근처의 스냅샷을 함께 찍어 준다 — 어느 값이 다른지 눈으로 보라고.
func TestPlayTraceParity(t *testing.T) {
	g := loadGolden(t)
	game := &Game{}
	for _, want := range g.Traces {
		got := RunTrace(game, want.Seed, want.Steps)

		if got.Restarts != want.Restarts {
			t.Errorf("시드 %d: 재시작이 %d회 — 정답은 %d회다", want.Seed, got.Restarts, want.Restarts)
		}
		if len(got.BH) != len(want.BH) {
			t.Fatalf("시드 %d: 스텝 수가 %d — 정답은 %d다", want.Seed, len(got.BH), len(want.BH))
		}

		for i := range want.BH {
			if got.BH[i] != want.BH[i] || got.SH[i] != want.SH[i] {
				t.Errorf("시드 %d: %d번째 스텝에서 갈라졌다\n"+
					"  보드 해시 %d (정답 %d)\n  stats 해시 %d (정답 %d)",
					want.Seed, i, got.BH[i], want.BH[i], got.SH[i], want.SH[i])
				reportNearestSnap(t, got, want, i)
				break
			}
		}

		// 해시가 다 맞아도 스냅샷을 따로 본다. 해시 충돌은 사실상 없지만,
		// 어느 필드가 무슨 값인지 사람이 읽을 수 있는 형태로 남겨 두는 편이 낫다.
		for si, ws := range want.Snaps {
			if si >= len(got.Snaps) {
				t.Fatalf("시드 %d: 스냅샷이 %d장뿐이다", want.Seed, len(got.Snaps))
			}
			gs := got.Snaps[si]
			if gs.I != ws.I {
				t.Fatalf("시드 %d: 스냅샷 %d 의 스텝 번호가 %d — 정답은 %d다",
					want.Seed, si, gs.I, ws.I)
			}
			for k := range ws.Stats {
				if gs.Stats[k] != ws.Stats[k] {
					t.Errorf("시드 %d 스텝 %d: stats[%d] = %d — 정답은 %d다",
						want.Seed, ws.I, k, gs.Stats[k], ws.Stats[k])
				}
			}
		}
	}
}

// reportNearestSnap 은 갈라진 스텝 바로 앞의 스냅샷을 통째로 찍는다.
// "해시가 다르다"만으로는 고칠 수가 없다 — 어떤 숫자가 다른지 봐야 한다.
func reportNearestSnap(t *testing.T, got TraceResult, want goldenTrace, step int) {
	t.Helper()
	si := step / SnapEvery
	if si >= len(got.Snaps) || si >= len(want.Snaps) {
		return
	}
	gs, ws := got.Snaps[si], want.Snaps[si]
	names := statNames()
	for k := range ws.Stats {
		if gs.Stats[k] != ws.Stats[k] {
			t.Logf("  스텝 %d 시점 %s: %d (정답 %d)", ws.I, names[k], gs.Stats[k], ws.Stats[k])
		}
	}
}

// statNames 는 Pack() 배열의 각 자리 이름. 실패 메시지를 사람이 읽을 수 있게 한다.
func statNames() [StatCount]string {
	return [StatCount]string{
		"Score", "Lines", "Level", "Combo", "B2B", "State", "Hold",
		"Next0", "Next1", "Next2", "Next3", "Next4",
		"Clear", "TSpin", "Gain", "Pieces", "Elapsed", "Gravity",
		"Piece", "Rot", "X", "Y", "Ghost", "Event", "RowMask",
		"Perfect", "LockPct", "Attack", "Pending", "GarbageRecv",
	}
}

// 2) 배치 트레이스 — 판 5 × 조각 7 × 단어 56. SRS 킥과 T스핀 판정의 정면 대조.
func TestPlacementTraceParity(t *testing.T) {
	g := loadGolden(t)
	game := &Game{}
	got := RunPlacementTrace(game, 0x2545f491)

	if len(got) != len(g.Placement) {
		t.Fatalf("배치 경우가 %d개 — 정답은 %d개다", len(got), len(g.Placement))
	}
	bad := 0
	for i, w := range g.Placement {
		c := got[i]
		if c.B != w.B || c.P != w.P || c.Wd != w.Wd {
			t.Fatalf("%d번 경우의 좌표가 (%d,%d,%d) — 정답은 (%d,%d,%d)다",
				i, c.B, c.P, c.Wd, w.B, w.P, w.Wd)
		}
		mine := append([]int64{int64(c.Hash)}, toInt64(c.R[:])...)
		for k := range w.R {
			if mine[k] != w.R[k] {
				if bad < 5 { // 다섯 개까지만 찍는다 — 다 찍으면 로그가 수만 줄이 된다
					t.Errorf("판%d %s 단어%d: %s 가 %d — 정답은 %d다",
						w.B, PieceNames[w.P], w.Wd, placementFieldNames[k], mine[k], w.R[k])
				}
				bad++
				break
			}
		}
	}
	if bad > 0 {
		t.Errorf("배치 경우 %d개 중 %d개가 어긋났다", len(got), bad)
	}
}

var placementFieldNames = [8]string{
	"보드해시", "점수", "지운줄", "T스핀", "상태", "공격", "누적줄", "B2B",
}

// 3) 연쇄 트레이스 — 콤보·B2B·레벨업·가비지 상쇄. 여러 락이 이어져야 드러나는 규칙들.
func TestComboTraceParity(t *testing.T) {
	g := loadGolden(t)
	game := &Game{}
	got := RunComboTrace(game, 0x13579bdf)

	if len(got) != len(g.Combo) {
		t.Fatalf("연쇄 라운드가 %d개 — 정답은 %d개다", len(got), len(g.Combo))
	}
	names := ComboScenarios()
	for i, w := range g.Combo {
		c := got[i]
		if c.S != w.S || c.I != w.I {
			t.Fatalf("%d번 라운드의 좌표가 (%d,%d) — 정답은 (%d,%d)다", i, c.S, c.I, w.S, w.I)
		}
		mine := append([]int64{int64(c.Hash)}, toInt64(c.R[:])...)
		for k := range w.R {
			if mine[k] != w.R[k] {
				t.Errorf("%q %d라운드: %s 가 %d — 정답은 %d다",
					names[w.S].Name, w.I, comboFieldNames[k], mine[k], w.R[k])
				break
			}
		}
	}
}

var comboFieldNames = [12]string{
	"보드해시", "점수", "이번획득", "지운줄", "T스핀", "콤보",
	"B2B", "레벨", "누적줄", "공격", "대기", "퍼펙트",
}

func toInt64(xs []int32) []int64 {
	out := make([]int64, len(xs))
	for i, v := range xs {
		out[i] = int64(v)
	}
	return out
}

// 트레이스가 실제로 흥미로운 곳을 밟는지 확인한다.
// 전부 통과했는데 알고 보니 아무 일도 안 일어난 트레이스였다면 검증한 게 없는 것이다.
func TestTracesActuallyExerciseTheRules(t *testing.T) {
	game := &Game{}
	cases := RunPlacementTrace(game, 0x2545f491)
	var cleared, tspins int
	for _, c := range cases {
		if c.R[1] > 0 { // 지운 줄
			cleared++
		}
		if c.R[2] > 0 { // T스핀
			tspins++
		}
	}
	t.Logf("배치 트레이스 %d경우 — 줄 지움 %d, T스핀 %d", len(cases), cleared, tspins)
	if cleared == 0 {
		t.Error("배치 트레이스에서 줄이 한 번도 안 지워졌다")
	}
	if tspins == 0 {
		t.Error("배치 트레이스에서 T스핀이 한 번도 안 나왔다")
	}

	steps := RunComboTrace(game, 0x13579bdf)
	var maxCombo, maxLevel, b2bHits int32
	for _, s := range steps {
		if s.R[4] > maxCombo {
			maxCombo = s.R[4]
		}
		if s.R[6] > maxLevel {
			maxLevel = s.R[6]
		}
		if s.R[5] == 1 {
			b2bHits++
		}
	}
	t.Logf("연쇄 트레이스 %d라운드 — 최대콤보 %d, 최대레벨 %d, B2B %d회",
		len(steps), maxCombo, maxLevel, b2bHits)
	if maxCombo < 2 || maxLevel < 2 || b2bHits == 0 {
		t.Error("연쇄 트레이스가 콤보·레벨업·B2B 를 제대로 안 밟았다")
	}
}
