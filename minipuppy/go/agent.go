package minipuppy

import (
	"context"
	"encoding/json"
	"fmt"
	"strings"
	"time"
)

// StopReason 은 루프가 왜 멈췄는가.
type StopReason string

const (
	StopDone       StopReason = "done"
	StopMaxSteps   StopReason = "max_steps"
	StopCancelled  StopReason = "cancelled"
	StopModelError StopReason = "model_error"
)

// RunResult 는 한 번 돌린 결과.
type RunResult struct {
	Text        string
	Steps       int
	ToolCalls   int
	Stopped     StopReason
	Err         string
	Seconds     float64
	Compactions int
}

// Limits 는 루프가 지킬 숫자들. 설정에서 채운다.
type Limits struct {
	ContextWindow       int
	CompactionThreshold float64
	ProtectedTokens     int
	MaxToolOutput       int
	MaxSteps            int
}

func DefaultLimits() Limits {
	return Limits{ContextWindow: 16000, CompactionThreshold: 0.75,
		ProtectedTokens: 2000, MaxToolOutput: 8000, MaxSteps: 20}
}

// Agent 하나 = 이름 + 시스템 프롬프트 + 도구 허용 목록 + 모델.
type Agent struct {
	Name        string
	DisplayName string
	System      string
	Model       Model
	Tools       []string // nil 이면 전부 허용
	Registry    *Registry
	Bus         *Bus
	Limits      Limits
}

func (a *Agent) NewHistory() *History { return NewHistory(a.System) }

func (a *Agent) emit(kind Kind, text string, kv ...string) {
	if a.Bus != nil {
		a.Bus.Emit(kind, text, kv...)
	}
}

// Run 이 이 프로그램의 심장이다.
//
//	걸음마다: 모델에 묻는다 -> 도구를 안 불렀으면 끝
//	          불렀으면 실행하고 결과를 기록에 붙이고 다시 위로
//
// 나머지는 전부 이 루프를 안 죽게 만드는 장치다. 특히 도구 오류를 error 로
// 올려 보내지 않고 **기록에 결과로 붙인다** — 모델이 오류 문구를 읽고 스스로
// 고치게 하려고. 여기서 루프를 끝내면 자가 수리가 불가능해진다.
func (a *Agent) Run(ctx context.Context, prompt string, h *History,
	ws *Workspace) (RunResult, *History) {
	if h == nil {
		h = a.NewHistory()
	}
	lim := a.Limits
	if lim.ContextWindow == 0 {
		lim = DefaultLimits()
	}
	started := time.Now()
	res := RunResult{Stopped: StopDone}
	if prompt != "" {
		h.User(prompt)
		a.emit(KindUser, prompt)
	}

	for step := 1; step <= lim.MaxSteps; step++ {
		select {
		case <-ctx.Done(): // 걸음 사이에서만 멈춘다 — 도구 중간에 끊으면 파일이 반쯤 쓰인다
			res.Stopped = StopCancelled
			res.Seconds = since(started)
			return res, h
		default:
		}
		res.Steps = step
		if h.NeedsCompaction(lim.ContextWindow, lim.CompactionThreshold) {
			if n, _ := h.Compact(lim.ProtectedTokens); n > 0 {
				res.Compactions++
				a.emit(KindSystem, fmt.Sprintf("기록 %d건을 접었다 (%d토큰 남음)",
					n, h.TotalTokens()))
			}
		}
		reply, err := a.Model.Complete(ctx, ToWire(h), a.Registry.Schemas(a.Tools))
		if err != nil {
			res.Stopped, res.Err = StopModelError, err.Error()
			a.emit(KindError, "모델 호출 실패: "+err.Error())
			res.Seconds = since(started)
			return res, h
		}
		if !reply.WantsTools() {
			h.Assistant(reply.Text)
			res.Text = reply.Text
			a.emit(KindAgent, reply.Text)
			res.Seconds = since(started)
			return res, h
		}
		for _, call := range reply.ToolCalls {
			a.runTool(call, h, ws, lim, &res)
		}
	}
	res.Stopped = StopMaxSteps
	a.emit(KindWarn, fmt.Sprintf("%d걸음을 다 썼다. 여기서 멈춘다.", lim.MaxSteps))
	res.Seconds = since(started)
	return res, h
}

func (a *Agent) runTool(call ToolCall, h *History, ws *Workspace,
	lim Limits, res *RunResult) {
	res.ToolCalls++
	raw, _ := json.Marshal(call.Args)
	h.ToolCall(call.ID, call.Name, string(raw))
	a.emit(KindTool, fmt.Sprintf("%s(%s)", call.Name, brief(call.Args)), "tool", call.Name)

	out := a.Registry.Call(ws, call.Name, call.Args, a.Tools, lim.MaxToolOutput)
	body := out.Content
	kind := KindToolOut
	if !out.OK {
		body = "오류: " + out.Content
		kind = KindWarn
	}
	h.ToolResult(call.ID, call.Name, body)
	a.emit(kind, body, "tool", call.Name)
}

func since(t time.Time) float64 {
	return float64(int(time.Since(t).Seconds()*1000)) / 1000
}

// ToWire 는 내부 Msg 를 모델 API 가 받는 모양으로 옮긴다.
func ToWire(h *History) []map[string]any {
	out := make([]map[string]any, 0, len(h.Msgs))
	for _, m := range h.Msgs {
		switch {
		case m.Role == RoleTool:
			out = append(out, map[string]any{"role": "tool",
				"tool_call_id": m.ToolCallID, "name": m.ToolName, "content": m.Content})
		case m.Role == RoleAssistant && m.ToolName != "":
			out = append(out, map[string]any{"role": "assistant", "content": nil,
				"tool_calls": []map[string]any{{"id": m.ToolCallID, "type": "function",
					"function": map[string]any{"name": m.ToolName, "arguments": m.ToolArgs}}}})
		default:
			out = append(out, map[string]any{"role": string(m.Role), "content": m.Content})
		}
	}
	return out
}

func brief(args map[string]any) string {
	keys := make([]string, 0, len(args))
	for k := range args {
		keys = append(keys, k)
	}
	sortStrings(keys)
	var parts []string
	for _, k := range keys {
		s := fmt.Sprint(args[k])
		s = strings.ReplaceAll(s, "\n", "⏎")
		if len([]rune(s)) > 60 {
			s = string([]rune(s)[:60]) + "…"
		}
		parts = append(parts, k+"="+s)
	}
	return strings.Join(parts, ", ")
}

func sortStrings(s []string) {
	for i := 1; i < len(s); i++ {
		for j := i; j > 0 && s[j] < s[j-1]; j-- {
			s[j], s[j-1] = s[j-1], s[j]
		}
	}
}
