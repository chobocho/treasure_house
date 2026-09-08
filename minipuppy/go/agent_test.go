package minipuppy

import (
	"context"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// 끝없이 같은 도구만 부른다. 걸음 제한이 없으면 영원히 돈다.
type loopModel struct{ count int }

func (l *loopModel) Name() string { return "무한" }
func (l *loopModel) Complete(_ context.Context, _ []map[string]any,
	_ []map[string]any) (Reply, error) {
	l.count++
	return CallTool("list_files", nil), nil
}

type deadModel struct{}

func (deadModel) Name() string { return "터짐" }
func (deadModel) Complete(_ context.Context, _ []map[string]any,
	_ []map[string]any) (Reply, error) {
	return Reply{}, &ModelError{Msg: "502 Bad Gateway", Retryable: true}
}

func agentWith(t *testing.T, m Model, tools []string) (*Agent, *Workspace, *Collector) {
	t.Helper()
	r, ws := tempWorkspace(t)
	RegisterShellTools(r, 0)
	col := NewCollector()
	return &Agent{Name: "t", System: "너는 시험용이다.", Model: m, Registry: r,
		Tools: tools, Bus: NewBus(col.Sink), Limits: DefaultLimits()}, ws, col
}

func TestSingleStepWhenNoTools(t *testing.T) {
	a, ws, _ := agentWith(t, NewScripted("s", Say("다 했다")), nil)
	res, h := a.Run(context.Background(), "안녕", nil, ws)
	if res.Text != "다 했다" || res.Steps != 1 || res.ToolCalls != 0 {
		t.Fatalf("한 걸음이 아니다: %+v", res)
	}
	if len(h.Msgs) != 3 {
		t.Fatalf("기록이 이상하다: %d건", len(h.Msgs))
	}
}

func TestToolResultGoesBackToModel(t *testing.T) {
	s := NewScripted("s",
		CallTool("read_file", map[string]any{"path": "src/b.go"}),
		Say("x 는 1 이다"))
	a, ws, col := agentWith(t, s, nil)
	res, h := a.Run(context.Background(), "b.go 보여줘", nil, ws)
	if res.Steps != 2 || res.ToolCalls != 1 {
		t.Fatalf("두 걸음이 아니다: %+v", res)
	}
	roles := ""
	for _, m := range h.Msgs {
		roles += string(m.Role[:1]) // system,user,assistant,tool,assistant
	}
	if roles != "suata" {
		t.Fatalf("역할 순서가 틀렸다: %s", roles)
	}
	// 두 번째 호출 때 모델은 도구 결과를 봤다
	last := s.Seen[1][len(s.Seen[1])-1]
	if last["role"] != "tool" {
		t.Fatalf("도구 결과가 안 넘어갔다: %v", last)
	}
	kinds := col.Kinds()
	if kinds[0] != KindUser || kinds[len(kinds)-1] != KindAgent {
		t.Fatalf("버스에 흐른 사건이 이상하다: %v", kinds)
	}
}

// 도구 실패는 error 로 올리지 않고 기록에 결과로 붙인다 — 모델이 스스로 고치게.
func TestToolFailureIsFedBackNotFatal(t *testing.T) {
	s := NewScripted("s",
		CallTool("read_file", map[string]any{"path": "없는파일.go"}),
		Say("없다고 하네"))
	a, ws, _ := agentWith(t, s, nil)
	res, h := a.Run(context.Background(), "보여줘", nil, ws)
	if res.Stopped != StopDone || res.Text != "없다고 하네" {
		t.Fatalf("루프가 죽었다: %+v", res)
	}
	if !strings.Contains(h.Msgs[3].Content, "오류") {
		t.Fatalf("오류가 기록에 안 붙었다: %q", h.Msgs[3].Content)
	}
}

func TestMaxStepsBreaksInfiniteLoop(t *testing.T) {
	m := &loopModel{}
	a, ws, _ := agentWith(t, m, nil)
	a.Limits.MaxSteps = 5
	res, _ := a.Run(context.Background(), "돌아라", nil, ws)
	if res.Stopped != StopMaxSteps || res.Steps != 5 || m.count != 5 {
		t.Fatalf("무한 루프가 안 끊겼다: %+v (count=%d)", res, m.count)
	}
}

func TestModelErrorStopsCleanly(t *testing.T) {
	a, ws, _ := agentWith(t, deadModel{}, nil)
	res, _ := a.Run(context.Background(), "안녕", nil, ws)
	if res.Stopped != StopModelError || !strings.Contains(res.Err, "502") {
		t.Fatalf("깨끗이 안 멈췄다: %+v", res)
	}
}

func TestCancelIsHeardBetweenSteps(t *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	a, ws, _ := agentWith(t, NewScripted("s", Say("올게")), nil)
	res, _ := a.Run(ctx, "가라", nil, ws)
	if res.Stopped != StopCancelled || res.ToolCalls != 0 {
		t.Fatalf("취소를 못 들었다: %+v", res)
	}
}

func TestAllowlistBlocksToolAtRuntime(t *testing.T) {
	s := NewScripted("s",
		CallTool("write_file", map[string]any{"path": "새것", "content": "x"}),
		Say("못 쓰는구나"))
	a, ws, _ := agentWith(t, s, ReadOnlyTools)
	res, h := a.Run(context.Background(), "파일 만들어", nil, ws)
	if !strings.Contains(h.Msgs[3].Content, "도구가 없다") {
		t.Fatalf("허용 목록이 안 막았다: %q", h.Msgs[3].Content)
	}
	if _, err := os.Stat(filepath.Join(ws.Root, "새것")); err == nil {
		t.Fatal("막았는데 파일이 생겼다")
	}
	if res.Stopped != StopDone {
		t.Fatalf("루프가 죽었다: %+v", res)
	}
}

func TestCompactionFiresWhenWindowOverflows(t *testing.T) {
	big := repeat("# 아주 긴 주석 한 줄이다\n", 400)
	r, ws := tempWorkspace(t)
	must(t, os.WriteFile(filepath.Join(ws.Root, "big.go"), []byte(big), 0o644))
	var replies []Reply
	for i := 0; i < 6; i++ {
		replies = append(replies, CallTool("read_file", map[string]any{"path": "big.go"}))
	}
	replies = append(replies, Say("끝"))
	a := &Agent{Name: "t", System: "시험", Model: NewScripted("s", replies...),
		Registry: r, Bus: NewBus(),
		Limits: Limits{ContextWindow: 400, CompactionThreshold: 0.5,
			ProtectedTokens: 100, MaxToolOutput: 8000, MaxSteps: 10}}
	res, h := a.Run(context.Background(), "여러 번 읽어", nil, ws)
	if res.Compactions == 0 {
		t.Fatalf("컴팩션이 안 돌았다: %+v (%d토큰)", res, h.TotalTokens())
	}
	if h.Msgs[0].Role != RoleSystem {
		t.Fatal("시스템 프롬프트가 사라졌다")
	}
}

func TestToWireShapesToolCalls(t *testing.T) {
	h := NewHistory("시스템")
	h.User("해봐")
	h.ToolCall("c1", "grep", `{"needle":"x"}`)
	h.ToolResult("c1", "grep", "a.go:1: x")
	wire := ToWire(h)
	calls := wire[2]["tool_calls"].([]map[string]any)
	fn := calls[0]["function"].(map[string]any)
	if fn["name"] != "grep" {
		t.Fatalf("도구 이름이 안 갔다: %v", fn)
	}
	if wire[3]["role"] != "tool" || wire[3]["tool_call_id"] != "c1" {
		t.Fatalf("도구 결과 모양이 틀렸다: %v", wire[3])
	}
}
