// 규칙을 어기는 실행기 일곱 — 처리기는 무엇을 잡고, 무엇을 저장하나.
//
//	go run ./09/rules
package main

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"iter"
	"log/slog"
	"net/http"
	"net/http/httptest"
	"strings"
	"time"

	"github.com/a2aproject/a2a-go/v2/a2a"
	"github.com/a2aproject/a2a-go/v2/a2asrv"
	"github.com/a2aproject/a2a-go/v2/a2asrv/taskstore"
)

type exec = func(*a2asrv.ExecutorContext,
	func(a2a.Event, error) bool)

func say(ec *a2asrv.ExecutorContext, text string) *a2a.Message {
	m := a2a.NewMessage(a2a.MessageRoleAgent, a2a.NewTextPart(text))
	m.ContextID = ec.ContextID
	return m
}

func task(ec *a2asrv.ExecutorContext, id a2a.TaskID) *a2a.Task {
	info := a2a.TaskInfo{TaskID: id, ContextID: ec.ContextID}
	return a2a.NewSubmittedTask(info, ec.Message)
}

// region: bad
var names = []string{"TwoMessages", "StatusFirst", "MessageAfterTask",
	"OtherId", "Silent", "Refuses", "Crashes"}

var bad = map[string]exec{
	"TwoMessages": func(ec *a2asrv.ExecutorContext,
		yield func(a2a.Event, error) bool) {
		_ = yield(say(ec, "하나"), nil) && yield(say(ec, "둘"), nil)
	},
	"StatusFirst": func(ec *a2asrv.ExecutorContext,
		yield func(a2a.Event, error) bool) { // Task 보다 상태가 먼저
		yield(a2a.NewStatusUpdateEvent(ec,
			a2a.TaskStateWorking, nil), nil)
	},
	"MessageAfterTask": func(ec *a2asrv.ExecutorContext,
		yield func(a2a.Event, error) bool) {
		_ = yield(task(ec, ec.TaskID), nil) &&
			yield(say(ec, "끝났습니다"), nil)
	},
	"OtherId": func(ec *a2asrv.ExecutorContext,
		yield func(a2a.Event, error) bool) { // 다른 id
		yield(task(ec, "my-own-id"), nil)
	},
	"Silent": func(*a2asrv.ExecutorContext,
		func(a2a.Event, error) bool) {
	}, // 아무것도 내놓지 않고 돌아간다
	"Refuses": func(ec *a2asrv.ExecutorContext,
		yield func(a2a.Event, error) bool) { // A2A 오류
		err := fmt.Errorf("인원이 없습니다: %w", a2a.ErrInvalidParams)
		yield(nil, err)
	},
	"Crashes": func(ec *a2asrv.ExecutorContext,
		yield func(a2a.Event, error) bool) { // 아무 오류
		yield(nil, errors.New("견적표를 못 읽었습니다"))
	},
}

// endregion

// region: try
// 실행기 하나마다 새 처리기 — JSON-RPC 처리기를 httptest 로 부른다
func fresh(name string, opts ...a2asrv.RequestHandlerOption,
) (*taskstore.InMemory, http.Handler) {
	store := taskstore.NewInMemory(&taskstore.InMemoryStoreConfig{
		Authenticator: func(context.Context) (string, error) {
			return "kim", nil // 목록을 보려고 주인을 한 사람으로
		},
	})
	f := func(ctx context.Context, ec *a2asrv.ExecutorContext,
	) iter.Seq2[a2a.Event, error] {
		return func(y func(a2a.Event, error) bool) { bad[name](ec, y) }
	}
	quiet := slog.New(slog.DiscardHandler) // SDK 의 기록은 끈다
	opts = append(opts, a2asrv.WithTaskStore(store),
		a2asrv.WithLogger(quiet))
	h := a2asrv.NewHandler(a2asrv.AgentExecutorFunc(f), opts...)
	return store, a2asrv.NewJSONRPCHandler(h)
}

// endregion

func saved(store *taskstore.InMemory) string {
	page, _ := store.List(context.Background(), &a2a.ListTasksRequest{})
	var s []string
	for _, t := range page.Tasks {
		s = append(s, string(t.Status.State))
	}
	return "[" + strings.Join(s, ", ") + "]"
}

const body = `{"jsonrpc":"2.0","id":1,"method":"%s","params":
  {"message":{"messageId":"m-1","role":"ROLE_USER",
  "parts":[{"text":"30"}]}}}`

// call 은 처리기를 2초까지 기다리고, 답 줄(SSE 면 data: 줄)을 읽는다.
// 네트워크 없이 httptest.ResponseRecorder 에 쓰게 한다.
func call(h http.Handler, method string) []string {
	ctx, stop := context.WithCancel(context.Background())
	req := httptest.NewRequestWithContext(ctx, "POST", "/",
		strings.NewReader(fmt.Sprintf(body, method)))
	rec := httptest.NewRecorder()
	done := make(chan struct{})
	go func() { h.ServeHTTP(rec, req); close(done) }()
	late := false
	select {
	case <-done:
	case <-time.After(2 * time.Second):
		late = true
		stop() // 요청을 거둔다 — 처리기가 돌아올 때까지 기다린다
		<-done
	}
	stop()
	var out []string
	for _, line := range strings.Split(rec.Body.String(), "\n") {
		line = strings.TrimPrefix(line, "data: ")
		if strings.HasPrefix(line, "{") {
			out = append(out, describe(line))
		}
	}
	if late {
		out = append(out, "✗ 2초 동안 끝나지 않는다")
	}
	if len(out) == 0 {
		out = append(out, "(아무것도 없다)")
	}
	return out
}

// describe 는 JSON-RPC 답 하나를 짧게 — result 의 키, 상태, 오류 코드.
func describe(line string) string {
	var r struct {
		Result map[string]struct {
			ID     string                  `json:"id"`
			Status struct{ State string }  `json:"status"`
			Parts  []struct{ Text string } `json:"parts"`
		}
		Error *struct {
			Code    int
			Message string
		}
	}
	_ = json.Unmarshal([]byte(line), &r)
	if r.Error != nil {
		return fmt.Sprintf("✗ %d %s", r.Error.Code, r.Error.Message)
	}
	for k, v := range r.Result {
		switch {
		case k == "message":
			return fmt.Sprintf("Message %q", v.Parts[0].Text)
		case v.ID == "my-own-id":
			return k + " my-own-id " + v.Status.State
		case v.Status.State != "":
			return k + " " + v.Status.State
		}
		return k
	}
	return line
}

func main() {
	for _, name := range names {
		store, h := fresh(name)
		fmt.Println(name)
		got := call(h, "SendMessage")
		fmt.Printf("  막는 호출  %s\n", strings.Join(got, " "))
		fmt.Printf("  저장       %s\n", saved(store))
		store, h = fresh(name)
		got = call(h, "SendStreamingMessage")
		fmt.Printf("  스트림     %s\n", strings.Join(got, " · "))
		_ = store
	}
	// region: timeout
	// 침묵하는 실행기에 "이벤트 사이 최대 0.5초" 를 걸면
	wait := a2asrv.WithAgentInactivityTimeout(500 * time.Millisecond)
	_, h := fresh("Silent", wait)
	fmt.Println("Silent + WithAgentInactivityTimeout(0.5초)")
	got := call(h, "SendMessage")
	fmt.Println("  막는 호출 ", strings.Join(got, " "))
	_, h = fresh("Silent", wait)
	got = call(h, "SendStreamingMessage")
	fmt.Println("  스트림    ", strings.Join(got, " · "))
	// endregion
}
