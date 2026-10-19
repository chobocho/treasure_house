// 정수 자리 손질(common.Int) 시험 — 수로 읽을 수 없는 값은 0 이 되어
// 업무 규칙이 거절해야 한다. 파이썬·TS 가 16부에서 맞춘 약속이다.
//
//	go run ./16/run_tests
package intstest

import (
	"testing"

	"example.com/workshop/agents/common"
	"example.com/workshop/workshop"
)

// SCENARIO §2.7
const badSize = "인원과 박 수는 1 이상이어야 합니다"

// region: tests
func TestInts(t *testing.T) {
	bad := map[string]any{"nights": 1.0, "headcount": "서른"}
	t.Run("numbers come back as ints", func(t *testing.T) {
		n, h := common.Int(1.0), common.Int("30")
		if n != 1 || h != 30 {
			t.Fatalf("got %d, %d", n, h)
		}
	})
	t.Run("not a number is zero", func(t *testing.T) {
		if h := common.Int(bad["headcount"]); h != 0 {
			t.Fatalf("got %d", h)
		}
	})
	t.Run("lodging rejects it", func(t *testing.T) {
		_, fail := workshop.ChooseLodging(workshop.LodgingRequest{
			Date:      "2026-10-30",
			Nights:    common.Int(bad["nights"]),
			Headcount: common.Int(bad["headcount"]),
		})
		if fail == nil || fail.Reason != badSize {
			t.Fatalf("got %+v", fail)
		}
	})
}

// endregion
