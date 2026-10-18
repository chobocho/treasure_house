// 기획 에이전트 시험 — 서버 없이 요청 처리기를 직접 부른다.
// agent.go 는 agents/planner/main.go 의 심볼릭 링크라 같은 package
// main 이 되고, 소문자 executor 가 보인다.
//
//	go run ./15/run_tests
//
// 명단(--agents)의 주소 11569 에는 아무도 없다 — 발견이 닿지 못한다.
package main

import (
	"context"
	"reflect"
	"strings"
	"testing"
	"time"

	"github.com/a2aproject/a2a-go/v2/a2a"
	"github.com/a2aproject/a2a-go/v2/a2asrv"

	"example.com/workshop/agents/common"
)

const dead = "http://127.0.0.1:11569/"

const story = "2026-10-30부터 1박 2일, 30명(채식 2명), " +
	"예산 6,000,000원, 출발 강남역"

// say 는 사용자 말 하나를 보내고 막는 호출의 Task 를 받는다.
func say(t *testing.T, text string) *a2a.Task {
	t.Helper()
	e := &executor{[]string{dead}, "planner", "planner-secret"}
	h := a2asrv.NewHandler(e)
	m := a2a.NewMessage(a2a.MessageRoleUser, a2a.NewTextPart(text))
	ctx, cancel := context.WithTimeout(context.Background(),
		10*time.Second)
	defer cancel()
	res, err := h.SendMessage(ctx, &a2a.SendMessageRequest{Message: m})
	if err != nil {
		t.Fatal(err)
	}
	task, ok := res.(*a2a.Task)
	if !ok {
		t.Fatalf("Task 대신 %T", res)
	}
	return task
}

// asked 는 되물은 DataPart 의 missing 목록이다.
func asked(t *testing.T, task *a2a.Task) any {
	t.Helper()
	if task.Status.State != a2a.TaskStateInputRequired {
		t.Fatalf("state = %s, want INPUT_REQUIRED", task.Status.State)
	}
	d, _ := task.Status.Message.Parts[1].Data().(map[string]any)
	return d["missing"]
}

// region: tests
func TestPlanner(t *testing.T) {
	want := []any{"headcount"}
	t.Run("message counted once", func(t *testing.T) {
		task := say(t, "2026-10-30 1박, 채식 2명, 예산 6,000,000원")
		if got := asked(t, task); !reflect.DeepEqual(got, want) {
			t.Errorf("missing = %v, want %v", got, want)
		}
	})
	t.Run("fullwidth digits are not a headcount", func(t *testing.T) {
		task := say(t, "2026-10-30 1박 ３０명, 예산 6,000,000원")
		if got := asked(t, task); !reflect.DeepEqual(got, want) {
			t.Errorf("missing = %v, want %v", got, want)
		}
	})
	t.Run("missing roles fail up front", func(t *testing.T) {
		task := say(t, story)
		if task.Status.State != a2a.TaskStateFailed {
			t.Fatalf("state = %s, want FAILED", task.Status.State)
		}
		why := common.TextOf(task.Status.Message)
		if why != "동료를 찾지 못했습니다: 숙소, 식사, 교통, 정산" {
			t.Errorf("까닭 = %q", why)
		}
		if strings.Contains(why, "127.0.0.1") {
			t.Error("안쪽 명단의 주소가 샜다")
		}
	})
}

// endregion
