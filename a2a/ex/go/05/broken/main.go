// 고장 에이전트 — 일하다 실패한다. 실패를 알리는 세 가지 길(6장):
//
//	직접 — 실행기가 FAILED 를 싣고 까닭을 status.message 에 적는다
//	나중 — Task·WORKING 을 실은 뒤 오류를 내보낸다
//	먼저 — 아무 이벤트도 싣기 전에 오류를 내보낸다
package main

import (
	"context"
	"errors"
	"iter"
	"log"

	"github.com/a2aproject/a2a-go/v2/a2a"
	"github.com/a2aproject/a2a-go/v2/a2asrv"

	"example.com/workshop/agents/common"
)

func card(url string) *a2a.AgentCard {
	return &a2a.AgentCard{
		Name:                "보물상사 고장 에이전트",
		Description:         "일하다 실패합니다.",
		Version:             "1.0.0",
		SupportedInterfaces: common.JSONRPCInterface(url),
		DefaultInputModes:   []string{"text/plain"},
		DefaultOutputModes:  []string{"text/plain"},
		Skills: []a2a.AgentSkill{{
			ID: "broken", Name: "고장", Tags: []string{"debug"},
		}},
	}
}

type broken struct{}

// region: execute
var errLedger = errors.New("장부 파일을 열 수 없습니다")

func (broken) Execute(
	ctx context.Context, ec *a2asrv.ExecutorContext,
) iter.Seq2[a2a.Event, error] {
	return func(yield func(a2a.Event, error) bool) {
		how := common.TextOf(ec.Message)
		common.Say("[고장] %s", how)
		if how == "먼저" { // 이벤트를 하나도 싣기 전에
			yield(nil, errLedger)
			return
		}
		_, up, ok := common.Begin(ec, yield) // SUBMITTED Task
		if !ok || !up.Status(a2a.TaskStateWorking) {
			return
		}
		if how == "나중" { // Task 를 실은 뒤에
			yield(nil, errLedger)
			return
		}
		// 직접: 실패도 상태 갱신이다 — 까닭을 메시지로
		why := common.TextPart("장부 파일을 열 수 없습니다")
		up.Status(a2a.TaskStateFailed, why)
	}
}

// endregion

func (broken) Cancel(
	ctx context.Context, ec *a2asrv.ExecutorContext,
) iter.Seq2[a2a.Event, error] {
	return common.Cancel(ec)
}

func main() {
	log.SetFlags(0) // SDK 기록(표준 오류)의 날짜·시각을 뺀다
	args := common.ParseArgs("보물상사 고장 에이전트")
	common.Serve(card(args.URL), broken{}, args.Port, common.Options{})
}

//@ norun
