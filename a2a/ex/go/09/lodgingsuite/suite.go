// Package lodgingsuite 는 숙소 실행기 시험 묶음이다 — HTTP 없이 요청
// 처리기를 직접 부른다. 실행기를 받는 함수라서, 같은 시험을 완성판
// (agents/lodging)과 3단계(09/step3_ask)에 돌린다.
package lodgingsuite

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"reflect"
	"testing"
	"time"

	"github.com/a2aproject/a2a-go/v2/a2a"
	"github.com/a2aproject/a2a-go/v2/a2asrv"

	"example.com/workshop/agents/common"
	"example.com/workshop/workshop"
)

type goldenCase struct {
	Name     string
	Input    any
	Expected any
}

func cases(t *testing.T) []goldenCase {
	raw, err := os.ReadFile(workshop.FixturePath("golden/domain.json"))
	if err != nil {
		t.Fatal(err)
	}
	var all map[string][]goldenCase
	if err := json.Unmarshal(raw, &all); err != nil {
		t.Fatal(err)
	}
	return all["chooseLodging"]
}

// region: fixture
// fixture 는 시험 하나의 처리기 — 시험마다 새 처리기·새 메모리
// 저장소라 작업을 나눠 갖지 않는다.
type fixture struct {
	t *testing.T
	h a2asrv.RequestHandler
	n int
}

func newFixture(t *testing.T, exec a2asrv.AgentExecutor) *fixture {
	return &fixture{t: t, h: a2asrv.NewHandler(exec)}
}

// say 는 사용자 말 하나를 보내고 막는 호출의 Task 를 받는다.
// task 가 있으면 그 작업에 이어 말한다.
func (f *fixture) say(task *a2a.Task, parts ...*a2a.Part) *a2a.Task {
	f.t.Helper()
	f.n++
	m := a2a.NewMessage(a2a.MessageRoleUser, parts...)
	m.ID = fmt.Sprintf("m-%d", f.n)
	if task != nil {
		m.TaskID, m.ContextID = task.ID, task.ContextID
	}
	// 침묵하는 실행기에 영영 묶이지 않게 — 처리기는 기다리기만 한다
	ctx, cancel := context.WithTimeout(context.Background(),
		5*time.Second)
	defer cancel()
	req := &a2a.SendMessageRequest{Message: m}
	res, err := f.h.SendMessage(ctx, req)
	if err != nil {
		f.t.Fatal(err)
	}
	got, ok := res.(*a2a.Task)
	if !ok {
		f.t.Fatalf("Task 대신 %T", res)
	}
	return got
}

// endregion

// 완료면 아티팩트의 DataPart, 아니면 상태 메시지의 까닭
func answerOf(t *a2a.Task) any {
	if t.Status.State == a2a.TaskStateCompleted {
		return t.Artifacts[0].Parts[0].Data()
	}
	return map[string]any{"ok": false,
		"reason": common.TextOf(t.Status.Message)}
}

func text(s string) *a2a.Part { return a2a.NewTextPart(s) }

// region: tests
// Run 은 시험 넷을 차례로 하위 시험(t.Run)으로 돌린다. 시험마다
// 새 처리기다.
func Run(t *testing.T, exec a2asrv.AgentExecutor) {
	tests := []struct {
		name string
		fn   func(*testing.T, *fixture)
	}{
		{"golden", golden},
		{"asks for first missing", asks},
		{"follow-up completes", followUp},
		{"hears only the user", hearsUser},
	}
	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			tc.fn(t, newFixture(t, exec))
		})
	}
}

func golden(t *testing.T, f *fixture) {
	for _, c := range cases(t) {
		t.Run(c.Name, func(t *testing.T) {
			f.t = t // 실패는 이 하위 시험에 적는다
			got := answerOf(f.say(nil, a2a.NewDataPart(c.Input)))
			if !reflect.DeepEqual(got, c.Expected) {
				t.Errorf("got %v\nwant %v", got, c.Expected)
			}
		})
	}
}

func asks(t *testing.T, f *fixture) {
	task := f.say(nil, text("숙소 부탁합니다"))
	asked := task.Status.Message.Parts[1].Data().(map[string]any)
	want := []any{"date", "nights", "headcount"}
	if !reflect.DeepEqual(asked["missing"], want) {
		t.Errorf("missing = %v, want %v", asked["missing"], want)
	}
}

// endregion

// region: dialog
func followUp(t *testing.T, f *fixture) {
	req := map[string]any{"date": "2026-10-30", "nights": 1.0}
	task := f.say(f.say(nil, a2a.NewDataPart(req)), text("30명"))
	total := answerOf(task).(map[string]any)["total"]
	if total != 2_100_000.0 {
		t.Errorf("total = %v, want 2100000", total)
	}
}

func hearsUser(t *testing.T, f *fixture) {
	task := f.say(nil, text("숙소 부탁합니다"))
	for _, line := range []string{"30명", "1박", "2026-11-06"} {
		// 끝난 작업에는 더 말할 수 없다
		if task.Status.State != a2a.TaskStateInputRequired {
			break
		}
		task = f.say(task, text(line))
	}
	venue := answerOf(task).(map[string]any)["venueId"]
	if venue != "chuncheon-lake" {
		t.Errorf("venueId = %v, want chuncheon-lake", venue)
	}
}

// endregion
