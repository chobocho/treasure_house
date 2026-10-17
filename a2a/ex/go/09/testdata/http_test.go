// 시험할 때만 agents/lodging 에 놓이는 파일 — HTTP 층의 시험.
package main

import (
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"

	"github.com/a2aproject/a2a-go/v2/a2a"
	"github.com/a2aproject/a2a-go/v2/a2aclient"
	"github.com/a2aproject/a2a-go/v2/a2aclient/agentcard"
	"github.com/a2aproject/a2a-go/v2/a2asrv"
)

// region: app
// app 은 common.Serve 의 짜임을 옮겨 적은 것 — Serve 는 짓기와
// 듣기(ListenAndServe)를 한 함수에서 해서 시험이 그대로 쓸 수 없다.
func app(url string) http.Handler {
	c := card(url)
	h := a2asrv.NewHandler(executor{},
		a2asrv.WithCapabilityChecks(&c.Capabilities))
	mux := http.NewServeMux()
	mux.Handle(a2asrv.WellKnownAgentCardPath,
		a2asrv.NewStaticAgentCardHandler(c))
	mux.Handle("/{$}", a2asrv.NewJSONRPCHandler(h))
	return mux
}

// rpc 는 소켓 없이 처리기를 부른다 — httptest.NewRecorder 가 응답을
// 받아 적는다.
func rpc(h http.Handler, method string, params any) string {
	body, _ := json.Marshal(map[string]any{"jsonrpc": "2.0",
		"id": 1, "method": method, "params": params})
	req := httptest.NewRequest("POST", "/",
		strings.NewReader(string(body)))
	req.Header.Set("Content-Type", "application/json")
	rec := httptest.NewRecorder()
	h.ServeHTTP(rec, req)
	return rec.Body.String()
}

// endregion

// region: wire
func TestWire(t *testing.T) {
	h := app("http://lodging.invalid/")
	t.Run("quote over JSON-RPC", func(t *testing.T) {
		msg := map[string]any{"messageId": "w-1", "role": "ROLE_USER",
			"parts": []any{map[string]any{"data": map[string]any{
				"date": "2026-10-30", "nights": 1, "headcount": 30}}}}
		got := rpc(h, "SendMessage", map[string]any{"message": msg})
		for _, want := range []string{`"TASK_STATE_COMPLETED"`,
			`"total":2100000`} { // 수가 JSON 에서도 정수인지
			if !strings.Contains(got, want) {
				t.Errorf("%s 이 없다: %s", want, got)
			}
		}
	})
	t.Run("unknown method", func(t *testing.T) {
		got := rpc(h, "FindLodging", map[string]any{})
		if !strings.Contains(got, `"code":-32601`) {
			t.Errorf("-32601 이 아니다: %s", got)
		}
	})
}

// endregion

// region: client
// SDK 클라이언트까지 — httptest.NewServer 가 127.0.0.1 의 빈 포트에
// 같은 프로세스 안에서 듣는다. 카드의 url 이 그 주소여야 한다.
func TestClient(t *testing.T) {
	var h http.Handler
	srv := httptest.NewServer(http.HandlerFunc(
		func(w http.ResponseWriter, r *http.Request) {
			h.ServeHTTP(w, r)
		}))
	t.Cleanup(srv.Close)
	h = app(srv.URL + "/")
	ctx := context.Background()
	card, err := agentcard.DefaultResolver.Resolve(ctx, srv.URL)
	if err != nil {
		t.Fatal(err)
	}
	c, err := a2aclient.NewFromCard(ctx, card)
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { c.Destroy() })
	m := a2a.NewMessage(a2a.MessageRoleUser,
		a2a.NewTextPart("숙소 부탁합니다"))
	var got []string
	for ev, err := range c.SendStreamingMessage(ctx,
		&a2a.SendMessageRequest{Message: m}) {
		if err != nil {
			t.Fatal(err)
		}
		switch e := ev.(type) {
		case *a2a.Task:
			got = append(got, "Task "+string(e.Status.State))
		case *a2a.TaskStatusUpdateEvent:
			got = append(got, "상태 "+string(e.Status.State))
		}
	}
	want := "Task TASK_STATE_SUBMITTED, 상태 TASK_STATE_INPUT_REQUIRED"
	if s := strings.Join(got, ", "); s != want {
		t.Errorf("이벤트 %s, want %s", s, want)
	}
}

// endregion
