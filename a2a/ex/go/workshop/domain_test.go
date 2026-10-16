// 골든 벡터 시험 — ex/fixtures/golden/domain.json 의 기대값과 한 글자도
// 다르면 안 된다. 같은 파일을 Python·TypeScript 시험도 읽는다.
package workshop

import (
	"encoding/json"
	"os"
	"reflect"
	"testing"
)

type goldenCase struct {
	Name     string          `json:"name"`
	Input    json.RawMessage `json:"input"`
	Expected json.RawMessage `json:"expected"`
}

// 결과를 JSON 으로 다시 풀어 비교한다 — Go 구조체의 필드 순서나
// 타입이 아니라, 와이어에 나가는 모양이 같은지를 본다.
func sameJSON(t *testing.T, got any, want json.RawMessage) {
	t.Helper()
	b, err := json.Marshal(got)
	if err != nil {
		t.Fatal(err)
	}
	var g, w any
	if err := json.Unmarshal(b, &g); err != nil {
		t.Fatal(err)
	}
	if err := json.Unmarshal(want, &w); err != nil {
		t.Fatal(err)
	}
	if !reflect.DeepEqual(g, w) {
		t.Errorf("got  %s\nwant %s", b, want)
	}
}

// either 는 (결과, 실패) 짝에서 실제로 나간 쪽 하나를 고른다.
func either[T any, F any](ok T, bad *F) any {
	if bad != nil {
		return bad
	}
	return ok
}

func run[In any](t *testing.T, key string, fn func(In) any) {
	raw, err := os.ReadFile("../../fixtures/golden/domain.json")
	if err != nil {
		t.Fatal(err)
	}
	var all map[string][]goldenCase
	if err := json.Unmarshal(raw, &all); err != nil {
		t.Fatal(err)
	}
	for _, c := range all[key] {
		t.Run(c.Name, func(t *testing.T) {
			var in In
			if err := json.Unmarshal(c.Input, &in); err != nil {
				t.Fatal(err)
			}
			sameJSON(t, fn(in), c.Expected)
		})
	}
}

func TestChooseLodging(t *testing.T) {
	run(t, "chooseLodging", func(r LodgingRequest) any {
		return either(ChooseLodging(r))
	})
}

func TestPlanMeals(t *testing.T) {
	run(t, "planMeals", func(r MealsRequest) any {
		return either(PlanMeals(r))
	})
}

func TestChooseBuses(t *testing.T) {
	run(t, "chooseBuses", func(r BusRequest) any {
		return either(ChooseBuses(r))
	})
}

func TestSettle(t *testing.T) {
	run(t, "settle", func(r SettleRequest) any {
		return either(Settle(r))
	})
}

func TestParseRequest(t *testing.T) {
	run(t, "parseRequest", func(s string) any {
		return either(ParseRequest(s))
	})
}
