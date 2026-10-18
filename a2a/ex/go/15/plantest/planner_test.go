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
	"encoding/json"
	"iter"
	"net"
	"net/http"
	"net/http/httptest"
	"reflect"
	"strings"
	"sync"
	"testing"
	"time"

	"github.com/a2aproject/a2a-go/v2/a2a"
	"github.com/a2aproject/a2a-go/v2/a2aclient"
	"github.com/a2aproject/a2a-go/v2/a2asrv"

	"example.com/workshop/agents/common"
	"example.com/workshop/workshop"
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

// fakeSettlement 는 가짜 정산이다 — 토큰을 주고, 첫 SendMessage 에는
// AUTH_REQUIRED 로 답하고, 받은 JSON-RPC 메서드를 적어 둔다.
type fakeSettlement struct {
	mu    sync.Mutex
	calls []string // "메서드 작업id"
}

func (f *fakeSettlement) ServeHTTP(w http.ResponseWriter,
	r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	if r.URL.Path == "/oauth/token" {
		w.Write([]byte(`{"access_token":"tok-fake"}`))
		return
	}
	var rpc struct {
		ID     any    `json:"id"`
		Method string `json:"method"`
		Params struct {
			ID string `json:"id"`
		} `json:"params"`
	}
	json.NewDecoder(r.Body).Decode(&rpc)
	f.mu.Lock()
	f.calls = append(f.calls, rpc.Method+" "+rpc.Params.ID)
	f.mu.Unlock()
	task := map[string]any{"id": "settle-1", "contextId": "c-1",
		"status": map[string]any{"state": "TASK_STATE_AUTH_REQUIRED"}}
	var result any = map[string]any{"task": task}
	if rpc.Method == "CancelTask" {
		task["status"] = map[string]any{
			"state": "TASK_STATE_CANCELED"}
		result = task
	}
	json.NewEncoder(w).Encode(map[string]any{
		"jsonrpc": "2.0", "id": rpc.ID, "result": result})
}

// region: settle-only
// settleOnly 는 견적 셋을 받은 셈 치고 정산부터 하는 기획 에이전트다.
// Go 에서는 결재 대기가 실행 안에 있어서(park.go) 진짜 서버로 띄운다.
type settleOnly struct {
	*executor
	card *a2a.AgentCard
}

func (s settleOnly) Execute(ctx context.Context,
	ec *a2asrv.ExecutorContext) iter.Seq2[a2a.Event, error] {
	return func(yield func(a2a.Event, error) bool) {
		task, up, ok := common.Begin(ec, yield)
		if !ok {
			return
		}
		budget := 6000000
		refs := []*a2a.Task{{ID: "l-1"}, {ID: "m-1"}, {ID: "b-1"}}
		items := []map[string]any{
			{"name": "숙소", "amount": 4842000}}
		s.settle(ctx, up, task, workshop.Parsed{Budget: &budget},
			s.card, refs, nil, items)
	}
}

// endregion

// denial 은 정산이 결재를 요구하게 한 뒤 "안 됩니다" 라고 답한다.
func denial(t *testing.T) (*a2a.Task, []string) {
	fake := &fakeSettlement{}
	srv := httptest.NewServer(fake)
	defer srv.Close()
	flow := a2a.ClientCredentialsOAuthFlow{
		TokenURL: srv.URL + "/oauth/token",
	}
	sc := &a2a.AgentCard{
		Name:                "가짜 정산",
		SupportedInterfaces: common.JSONRPCInterface(srv.URL + "/"),
		SecuritySchemes: a2a.NamedSecuritySchemes{
			"oauth": a2a.OAuth2SecurityScheme{Flows: flow},
		},
	}
	e := &executor{[]string{dead}, "planner", "planner-secret"}
	const url = "http://127.0.0.1:11566/"
	go common.Serve(card(url), settleOnly{e, sc}, 11566,
		common.Options{})
	for { // 서버가 뜰 때까지
		if c, err := net.Dial("tcp", "127.0.0.1:11566"); err == nil {
			c.Close()
			break
		}
		time.Sleep(50 * time.Millisecond)
	}
	ctx, cancel := context.WithTimeout(context.Background(),
		10*time.Second)
	defer cancel()
	client, err := a2aclient.NewFromCard(ctx, card(url),
		a2aclient.WithJSONRPCTransport(common.HTTPClient("")))
	if err != nil {
		t.Fatal(err)
	}
	m := a2a.NewMessage(a2a.MessageRoleUser, a2a.NewTextPart("정산"))
	var id a2a.TaskID
	for ev, err := range client.SendStreamingMessage(ctx,
		&a2a.SendMessageRequest{Message: m}) {
		if err != nil {
			t.Fatal(err)
		}
		id = ev.TaskInfo().TaskID // AUTH_REQUIRED 에서 스트림이 닫힌다
	}
	no := a2a.NewMessage(a2a.MessageRoleUser,
		a2a.NewTextPart("안 됩니다"))
	no.TaskID = id
	res, err := client.SendMessage(ctx,
		&a2a.SendMessageRequest{Message: no})
	if err != nil {
		t.Fatal(err)
	}
	task, _ := res.(*a2a.Task)
	fake.mu.Lock()
	defer fake.mu.Unlock()
	return task, fake.calls
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
	t.Run("denial cancels settlement", func(t *testing.T) {
		task, calls := denial(t)
		if task == nil || task.Status.State != a2a.TaskStateRejected {
			t.Fatalf("task = %v, want REJECTED", task)
		}
		// 반려하면 정산 쪽에서 기다리던 작업도 거둔다
		want := []string{"SendMessage ", "CancelTask settle-1"}
		if !reflect.DeepEqual(calls, want) {
			t.Errorf("정산이 받은 것 = %q, want %q", calls, want)
		}
	})
}

// endregion
