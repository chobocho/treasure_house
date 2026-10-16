// 고집 에이전트 — 상태를 앞뒤로 옮겨 보고, 끝난 뒤에도 옮겨 본다.
// SDK 가 어느 전이를 막는지 보려는 실험용이다(2장).
package main

import (
	"context"
	"iter"
	"log"
	"time"

	"github.com/a2aproject/a2a-go/v2/a2a"
	"github.com/a2aproject/a2a-go/v2/a2asrv"

	"example.com/workshop/agents/common"
)

func card(url string) *a2a.AgentCard {
	return &a2a.AgentCard{
		Name:                "보물상사 고집 에이전트",
		Description:         "상태를 마음대로 옮겨 봅니다.",
		Version:             "1.0.0",
		SupportedInterfaces: common.JSONRPCInterface(url),
		DefaultInputModes:   []string{"text/plain"},
		DefaultOutputModes:  []string{"text/plain"},
		Skills: []a2a.AgentSkill{{
			ID: "stubborn", Name: "고집", Tags: []string{"debug"},
		}},
	}
}

type stubborn struct{}

// region: execute
func (stubborn) Execute(
	ctx context.Context, ec *a2asrv.ExecutorContext,
) iter.Seq2[a2a.Event, error] {
	return func(yield func(a2a.Event, error) bool) {
		put := func(s a2a.TaskState) {
			// SDK 가 실행을 거두면 ctx 가 취소된다 — 먼저 그것을 본다
			if err := ctx.Err(); err != nil {
				common.Say("[고집] %s 거절: %v", s, err)
				return
			}
			ev := a2a.NewStatusUpdateEvent(ec, s, nil)
			// yield 가 false 면 SDK 가 "그만" 이라고 한 것이다
			if yield(ev, nil) {
				common.Say("[고집] %s 실음", s)
			} else {
				common.Say("[고집] %s 거절: yield 가 false", s)
			}
		}
		yield(a2a.NewSubmittedTask(ec, ec.Message), nil)
		// 앞으로, 뒤로(접수로 되돌리기), 끝 — 갱신기는 없다
		put(a2a.TaskStateWorking)
		put(a2a.TaskStateSubmitted)
		put(a2a.TaskStateCompleted)
		time.Sleep(200 * time.Millisecond) // 끝낸 뒤 조금 있다가
		put(a2a.TaskStateWorking)
	}
}

// endregion

func (stubborn) Cancel(
	ctx context.Context, ec *a2asrv.ExecutorContext,
) iter.Seq2[a2a.Event, error] {
	return common.Cancel(ec)
}

func main() {
	log.SetFlags(0) // SDK 기록(표준 오류)의 날짜·시각을 뺀다
	args := common.ParseArgs("보물상사 고집 에이전트")
	common.Serve(card(args.URL), stubborn{}, args.Port,
		common.Options{})
}

//@ norun
