// 종료 실험 에이전트 — 첫 글 파트로 고른 차례대로 상태를 싣고
// 돌아간다. SDK 가 스트림을 언제 닫는지 보려는 실험용이다(3장).
// 서버는 SDK 기본값 그대로다 — agents/common 의 Serve 는 AUTH_REQUIRED
// 에서 스트림을 닫는 덮개(waiter)를 씌우므로 여기서는 쓰지 않는다.
package main

import (
	"context"
	"errors"
	"fmt"
	"iter"
	"log"
	"net/http"
	"time"

	"github.com/a2aproject/a2a-go/v2/a2a"
	"github.com/a2aproject/a2a-go/v2/a2asrv"

	"example.com/workshop/agents/common"
)

// region: plans
// 고른 말 → 실행기가 싣는 상태들. "쉼" 은 0.3초 쉬기,
// "BOOM" 은 오류 내기. MESSAGE 는 Task 없이 Message 하나.
var plans = map[string][]string{
	"COMPLETED":      {"WORKING", "COMPLETED"},
	"INPUT_REQUIRED": {"INPUT_REQUIRED"},
	"AUTH_REQUIRED":  {"AUTH_REQUIRED"},
	"WORKING":        {"WORKING"}, // 끝 상태 없이 돌아간다
	"LATE":           {"INPUT_REQUIRED", "쉼", "WORKING", "COMPLETED"},
	"BOOM":           {"WORKING", "쉼", "BOOM"},
	"MESSAGE":        {},
}

// endregion

type closer struct{}

// region: execute
func (closer) Execute(
	ctx context.Context, ec *a2asrv.ExecutorContext,
) iter.Seq2[a2a.Event, error] {
	return func(yield func(a2a.Event, error) bool) {
		word := common.TextOf(ec.Message)
		if word == "MESSAGE" {
			part := common.TextPart("메시지로 답함")
			yield(a2a.NewMessage(a2a.MessageRoleAgent, part), nil)
			return
		}
		_, up, ok := common.Begin(ec, yield) // Task(SUBMITTED) 가 먼저
		for _, step := range plans[word] {
			switch step {
			case "쉼":
				time.Sleep(300 * time.Millisecond)
			case "BOOM":
				common.Say("[종료] %s: 오류를 낸다", word)
				yield(nil, errors.New("실행기가 죽었다"))
				return
			default:
				state := a2a.TaskState("TASK_STATE_" + step)
				ok = ok && up.Status(state)
			}
			if !ok { // yield 가 false — SDK 가 "그만" 이라고 했다
				break
			}
		}
		common.Say("[종료] %s: 실행기가 돌아갔다", word)
	}
}

// endregion

func (closer) Cancel(
	ctx context.Context, ec *a2asrv.ExecutorContext,
) iter.Seq2[a2a.Event, error] {
	return common.Cancel(ec)
}

// region: serve
// SDK 의 기본 옵션 그대로 — NewHandler 에 옵션을 주지 않는다.
func main() {
	log.SetFlags(0) // SDK 기록(표준 오류)의 날짜·시각을 뺀다
	args := common.ParseArgs("보물상사 종료 실험 에이전트")
	card := &a2a.AgentCard{
		Name:                "보물상사 종료 실험 에이전트",
		Description:         "고른 상태에서 실행을 끝냅니다.",
		Version:             "1.0.0",
		SupportedInterfaces: common.JSONRPCInterface(args.URL),
		Capabilities:        a2a.AgentCapabilities{Streaming: true},
		DefaultInputModes:   []string{"text/plain"},
		DefaultOutputModes:  []string{"text/plain"},
		Skills: []a2a.AgentSkill{{
			ID: "close", Name: "종료 실험", Tags: []string{"debug"},
		}},
	}
	mux := http.NewServeMux()
	mux.Handle(a2asrv.WellKnownAgentCardPath,
		a2asrv.NewStaticAgentCardHandler(card))
	h := a2asrv.NewHandler(closer{})
	mux.Handle("/{$}", a2asrv.NewJSONRPCHandler(h))
	addr := fmt.Sprintf("127.0.0.1:%d", args.Port)
	log.Fatal(http.ListenAndServe(addr, mux))
}

// endregion

//@ norun
