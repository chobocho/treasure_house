package ai

import (
	_ "embed"
	"encoding/json"
	"fmt"
)

// 보드 평가에 쓰는 특징 8가지. **순서가 곧 가중치 배열의 순서다.**
//
// 이 순서는 1편·2편의 C++ AI(ai.cpp)와 유전 알고리즘이 학습한 가중치가 공유하는
// 약속이다. 하나라도 자리를 바꾸면 학습된 가중치가 전부 무의미해진다.
const (
	FLines = iota // 이 수로 지워지는 줄 수  (많을수록 좋다)
	FAgg          // 열 높이의 총합  (낮을수록 좋다)
	FHoles        // 덮인 빈칸 개수  (적을수록 좋다)
	FBump         // 이웃한 열 높이차의 총합  (작을수록 좋다)
	FWells        // 우물 깊이의 누적 비용  (작을수록 좋다)
	FRowT         // 행 전이 수 (Dellacherie)  (작을수록 좋다)
	FColT         // 열 전이 수 (Dellacherie)  (작을수록 좋다)
	FLand         // 조각이 놓인 높이  (낮을수록 좋다)
	FCount = 8
)

// FeatureNames 는 화면과 로그에 쓰는 이름.
var FeatureNames = [FCount]string{
	"F_LINES", "F_AGG", "F_HOLES", "F_BUMP", "F_WELLS", "F_ROWT", "F_COLT", "F_LAND",
}

// Weights 는 특징 8개에 곱하는 계수.
//
// float32 인 것이 중요하다. C++ 원본이 float 였고, 평가 점수의 마지막 비트 하나가
// 달라지면 argmax 가 다른 후보를 골라 그때부터 판이 통째로 갈라진다.
// float64 로 올리면 "더 정확해지는" 게 아니라 **다른 AI 가 된다**.
type Weights [FCount]float32

// weights.json 은 2편의 유전 알고리즘이 실제로 학습해 낸 결과다.
// 파일을 실행 파일 안에 박아 넣어서, 어디서 실행하든 같은 AI 가 되게 한다.
//
//go:embed weights.json
var weightsJSON []byte

// levels 는 파일을 딱 한 번만 파싱해서 담아 둔다.
// 파싱은 프로그램이 뜰 때 끝나야 한다 — 게임 중에 실패하면 손쓸 방법이 없다.
var levels = mustParseLevels()

func mustParseLevels() map[string]Weights {
	var doc struct {
		Features []string             `json:"features"`
		Levels   map[string][]float64 `json:"levels"`
	}
	if err := json.Unmarshal(weightsJSON, &doc); err != nil {
		panic(fmt.Sprintf("weights.json 을 읽을 수 없다: %v", err))
	}
	// 특징 이름과 순서가 파일과 코드에서 같은지 확인한다.
	// 순서가 어긋난 채로 돌면 AI 가 "구멍을 좋아하는" 괴물이 된다.
	if len(doc.Features) != FCount {
		panic(fmt.Sprintf("weights.json 의 특징이 %d개다 — %d개여야 한다", len(doc.Features), FCount))
	}
	for i, name := range doc.Features {
		if name != FeatureNames[i] {
			panic(fmt.Sprintf("weights.json 의 %d번 특징이 %q — %q 여야 한다", i, name, FeatureNames[i]))
		}
	}
	out := make(map[string]Weights, len(doc.Levels))
	for name, vals := range doc.Levels {
		if len(vals) != FCount {
			panic(fmt.Sprintf("난이도 %q 의 가중치가 %d개다", name, len(vals)))
		}
		var w Weights
		for i, v := range vals {
			w[i] = float32(v)
		}
		out[name] = w
	}
	for _, name := range LevelNames {
		if _, ok := out[name]; !ok {
			panic(fmt.Sprintf("weights.json 에 난이도 %q 가 없다", name))
		}
	}
	return out
}

// Levels 는 난이도별 가중치의 사본. easy / normal / hard / max.
func Levels() map[string]Weights {
	out := make(map[string]Weights, len(levels))
	for k, v := range levels {
		out[k] = v
	}
	return out
}

// Level 은 이름으로 가중치를 찾는다.
func Level(name string) (Weights, bool) {
	w, ok := levels[name]
	return w, ok
}

// LevelNames 는 쉬운 것부터 어려운 순서. 메뉴와 도움말이 이 순서를 쓴다.
var LevelNames = []string{"easy", "normal", "hard", "max"}
