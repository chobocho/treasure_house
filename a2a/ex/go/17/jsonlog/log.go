// Package jsonlog 는 요청 하나에 JSON 한 줄을 남긴다. HTTP 층의
// Middleware 가 줄을 열고 닫고, SDK 층의 Interceptor 가 형(type)이
// 있는 요청·응답으로 그 줄을 채운다. 줄은 $A2A_LOG 디렉터리의
// <에이전트>.jsonl 에 붙인다($A2A_LOG 가 없으면 $TMPDIR/a2a-log).
package jsonlog

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"sync"
	"time"

	"github.com/a2aproject/a2a-go/v2/a2a"
	"github.com/a2aproject/a2a-go/v2/a2asrv"
)

// region: line
// Line 은 로그 한 줄. 필드 차례가 곧 JSON 의 키 차례다.
type Line struct {
	T      string `json:"t"`
	Agent  string `json:"agent"`
	RPC    any    `json:"rpc"`
	Method any    `json:"method"`
	Msg    any    `json:"msg"`
	Ctx    any    `json:"ctx"`
	Task   any    `json:"task"`
	State  any    `json:"state"`
	Took   string `json:"took"`
}

// 빈 문자열은 null 로 — 파이썬·TS 의 줄과 같은 모양
func or(s string) any {
	if s == "" {
		return nil
	}
	return s
}

// endregion

type key struct{}

var mu sync.Mutex // 동시에 끝난 요청들이 한 파일에 붙인다

// region: middleware
// Middleware 는 JSON-RPC 처리기 앞에 서서 줄을 열고, 끝나면 적는다.
// JSON-RPC 의 id 는 이 층에서만 보인다.
func Middleware(agent string, next http.Handler) http.Handler {
	dir := os.Getenv("A2A_LOG")
	if dir == "" {
		dir = filepath.Join(os.TempDir(), "a2a-log")
	}
	_ = os.MkdirAll(dir, 0o755)
	file := filepath.Join(dir, agent+".jsonl")
	return http.HandlerFunc(func(
		w http.ResponseWriter, r *http.Request,
	) {
		began := time.Now()
		body, _ := io.ReadAll(r.Body)
		r.Body = io.NopCloser(bytes.NewReader(body)) // 되돌려 놓는다
		var head struct{ ID any }
		_ = json.Unmarshal(body, &head)
		rec := &Line{T: began.UTC().Format(time.RFC3339Nano),
			Agent: agent, RPC: head.ID}
		ctx := context.WithValue(r.Context(), key{}, rec)
		next.ServeHTTP(w, r.WithContext(ctx))
		ms := float64(time.Since(began).Microseconds()) / 1000
		rec.Took = fmt.Sprintf("%.1fms", ms)
		raw, _ := json.Marshal(rec)
		mu.Lock()
		defer mu.Unlock()
		f, err := os.OpenFile(file,
			os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0o644)
		if err == nil {
			_, _ = f.Write(append(raw, '\n'))
			_ = f.Close()
		}
	})
}

// endregion

// region: before
// Interceptor 는 SDK 의 CallInterceptor 다. Before·After 가 받는 값은
// 이미 a2a 패키지의 형으로 풀려 있다. 스트림이면 After 가 이벤트마다
// 불리므로, 마지막 이벤트의 상태가 줄에 남는다.
type Interceptor struct{}

func (Interceptor) Before(ctx context.Context, cc *a2asrv.CallContext,
	req *a2asrv.Request) (context.Context, any, error) {
	if rec, ok := ctx.Value(key{}).(*Line); ok {
		rec.Method = cc.Method()
		switch p := req.Payload.(type) {
		case *a2a.SendMessageRequest:
			if m := p.Message; m != nil {
				rec.Msg, rec.Ctx = or(m.ID), or(m.ContextID)
				rec.Task = or(string(m.TaskID))
			}
		case *a2a.GetTaskRequest:
			rec.Task = or(string(p.ID))
		case *a2a.CancelTaskRequest:
			rec.Task = or(string(p.ID))
		case *a2a.SubscribeToTaskRequest:
			rec.Task = or(string(p.ID))
		}
	}
	return ctx, nil, nil
}

// endregion

// region: after
func (Interceptor) After(ctx context.Context, cc *a2asrv.CallContext,
	resp *a2asrv.Response) error {
	rec, ok := ctx.Value(key{}).(*Line)
	if !ok {
		return nil
	}
	if resp.Err != nil {
		rec.State = "error: " + resp.Err.Error()
	}
	switch p := resp.Payload.(type) {
	case *a2a.Task:
		rec.Ctx, rec.Task = or(p.ContextID), or(string(p.ID))
		rec.State = string(p.Status.State)
	case *a2a.Message:
		rec.Ctx, rec.Task = or(p.ContextID), or(string(p.TaskID))
	case *a2a.TaskStatusUpdateEvent:
		rec.Ctx, rec.Task = or(p.ContextID), or(string(p.TaskID))
		rec.State = string(p.Status.State)
	case *a2a.TaskArtifactUpdateEvent:
		rec.Ctx, rec.Task = or(p.ContextID), or(string(p.TaskID))
	}
	return nil
}

// endregion
