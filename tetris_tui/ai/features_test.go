package ai

import (
	"testing"

	"treasure/tetris_tui/core"
)

func paint(rows ...string) *core.Board {
	var b core.Board
	b.Paint(rows)
	return &b
}

func rep(row string, n int) []string {
	out := make([]string, n)
	for i := range out {
		out[i] = row
	}
	return out
}

// 빈 판의 특징. 높이도 구멍도 우물도 0 이고, 전이 수만 판 크기에서 나온다.
//
//	행 전이: 줄마다 왼쪽 벽(채움) → 빈칸 = 1, 오른쪽 벽에서 다시 1 → 줄당 2, 24줄 = 48
//	열 전이: 천장 위는 빈칸, 바닥은 채움 → 열당 1, 10열 = 10
func TestEmptyBoardFeatures(t *testing.T) {
	f := Features(paint(), 0, 0)
	want := [FCount]float32{0, 0, 0, 0, 0, 48, 10, 0}
	if f != want {
		t.Errorf("빈 판의 특징이 %v — %v 를 기대했다", f, want)
	}
}

// 가득 찬 판. 높이 24×10 = 240, 구멍 0.
//
//	행 전이: 줄마다 벽부터 끝까지 전부 채움 → 전이 0
//	열 전이: 천장 위(빈칸) → 첫 칸(채움) 에서 1, 바닥은 채움이라 추가 없음 → 열당 1
func TestFullBoardFeatures(t *testing.T) {
	f := Features(paint(rep("##########", core.H)...), 0, 0)
	if f[FAgg] != float32(core.H*core.W) {
		t.Errorf("높이 합이 %v — %d 를 기대했다", f[FAgg], core.H*core.W)
	}
	if f[FHoles] != 0 {
		t.Errorf("구멍이 %v 개다", f[FHoles])
	}
	if f[FRowT] != 0 {
		t.Errorf("행 전이가 %v 다 — 꽉 찬 판은 0 이다", f[FRowT])
	}
	if f[FColT] != float32(core.W) {
		t.Errorf("열 전이가 %v 다 — %d 를 기대했다", f[FColT], core.W)
	}
}

// 구멍의 정의: "그 열에서 가장 높은 블록보다 아래에 있는 빈칸".
// 옆이 뚫려 있어도 위가 덮여 있으면 구멍이다.
func TestHolesAreCoveredEmptyCells(t *testing.T) {
	f := Features(paint("#.........", "..........", "#........."), 0, 0)
	// 0열: 맨 위 블록 아래로 빈칸 하나(가운데 줄) → 구멍 1
	if f[FHoles] != 1 {
		t.Errorf("구멍이 %v 개다 — 1개여야 한다", f[FHoles])
	}
	// 덮이지 않은 빈칸은 구멍이 아니다
	f2 := Features(paint("..........", "#........."), 0, 0)
	if f2[FHoles] != 0 {
		t.Errorf("덮이지 않은 빈칸이 구멍으로 세어졌다: %v", f2[FHoles])
	}
}

// 울퉁불퉁함 = 이웃한 열 높이차의 절댓값 합.
func TestBumpiness(t *testing.T) {
	// 계단 판: 높이 3,2,1,0,0,0,0,0,0,0 → |3-2|+|2-1|+|1-0| = 3
	f := Features(paint("#.........", "##........", "###......."), 0, 0)
	if f[FBump] != 3 {
		t.Errorf("울퉁불퉁함이 %v — 3 을 기대했다", f[FBump])
	}
	// 평평한 판은 0
	f2 := Features(paint(rep("##########", 5)...), 0, 0)
	if f2[FBump] != 0 {
		t.Errorf("평평한 판의 울퉁불퉁함이 %v 다", f2[FBump])
	}
}

// 우물: 양옆보다 깊게 파인 만큼. 비용은 1+2+…+d 로 깊을수록 급격히 커진다.
// 벽은 천장 높이로 친다 — 그래야 "벽에 붙은 1칸 우물"이 우물로 잡힌다.
func TestWellCostGrowsQuadratically(t *testing.T) {
	// 왼쪽 벽에 붙은 깊이 4짜리 우물 (오른쪽 열 높이 4, 왼쪽 열 높이 0)
	f := Features(paint(rep(".#########", 4)...), 0, 0)
	// 0열: 왼쪽은 벽(H), 오른쪽은 4 → min 4, 높이 0 → 깊이 4 → 4*5/2 = 10
	if f[FWells] != 10 {
		t.Errorf("깊이 4 우물의 비용이 %v — 10 을 기대했다", f[FWells])
	}
	f2 := Features(paint(rep(".#########", 2)...), 0, 0)
	if f2[FWells] != 3 { // 2*3/2
		t.Errorf("깊이 2 우물의 비용이 %v — 3 을 기대했다", f2[FWells])
	}
}

// 전달받은 lines 와 landH 는 그대로 특징 벡터에 실린다.
// (판에서 계산할 수 없는 값이라 호출자가 준다)
func TestLinesAndLandHeightArePassedThrough(t *testing.T) {
	f := Features(paint(), 3, 17)
	if f[FLines] != 3 || f[FLand] != 17 {
		t.Errorf("lines=%v land=%v", f[FLines], f[FLand])
	}
}

func TestScoreIsTheDotProduct(t *testing.T) {
	w := Weights{1, 2, 3, 4, 5, 6, 7, 8}
	f := [FCount]float32{1, 1, 1, 1, 1, 1, 1, 1}
	if got := Score(w, f); got != 36 {
		t.Errorf("점수가 %v — 36 을 기대했다", got)
	}
	if got := Score(Weights{}, f); got != 0 {
		t.Errorf("가중치가 전부 0 인데 점수가 %v 다", got)
	}
}

// weights.json 은 실행 파일 안에 박혀 있다. 없거나 깨지면 프로그램이 못 뜬다.
func TestEmbeddedLevels(t *testing.T) {
	lv := Levels()
	for _, name := range LevelNames {
		w, ok := lv[name]
		if !ok {
			t.Fatalf("난이도 %q 가 없다", name)
		}
		var zero Weights
		if w == zero {
			t.Errorf("난이도 %q 의 가중치가 전부 0 이다", name)
		}
	}
	if len(lv) != len(LevelNames) {
		t.Errorf("난이도가 %d개다 — %v 만 있어야 한다", len(lv), LevelNames)
	}
}

func TestLevelLookup(t *testing.T) {
	if _, ok := Level("hard"); !ok {
		t.Error("hard 를 못 찾았다")
	}
	if _, ok := Level("없는난이도"); ok {
		t.Error("없는 난이도가 찾아졌다")
	}
}

// 2편의 GA 가 학습한 값이라 부호에 뜻이 있다. max 가중치의 부호를 못 박아 둔다:
// 구멍·행전이·열전이·착지높이는 음수(피해야 할 것), 나머지는 양수여도 된다.
func TestMaxWeightsHaveTheExpectedSigns(t *testing.T) {
	w, _ := Level("max")
	for _, i := range []int{FHoles, FRowT, FColT, FLand} {
		if w[i] >= 0 {
			t.Errorf("%s 의 가중치가 %v 다 — 음수여야 한다", FeatureNames[i], w[i])
		}
	}
}
