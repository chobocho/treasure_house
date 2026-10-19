// 오류 시험대 — 완성 에이전트로는 일으킬 수 없는 오류를 일부러 낸다.
// 카드는 확장 카드 기능을 켰지만 확장 카드를 두지 않았다(-32007).
// 실행기는 받은 글에 따라 규칙을 어긴다:
//
//	"차례 위반" — Task 보다 상태 갱신을 먼저 싣는다(-32006)
//	"고장"      — 오류를 돌려준다(-32603)
//	그 밖       — 받은 글을 Message 로 돌려준다
//
//	go run ./16/bench --port P
package main

import (
	"context"
	"errors"
	"iter"

	"github.com/a2aproject/a2a-go/v2/a2a"
	"github.com/a2aproject/a2a-go/v2/a2asrv"

	"example.com/workshop/agents/common"
)

// region: card
func card(url string) *a2a.AgentCard {
	return &a2a.AgentCard{
		Name:                "보물상사 시험대 에이전트",
		Description:         "오류를 일부러 냅니다.",
		Version:             "1.0.0",
		SupportedInterfaces: common.JSONRPCInterface(url),
		// 확장 카드를 준다고 적고, 처리기에는 넘기지 않는다
		Capabilities: a2a.AgentCapabilities{
			Streaming: true, ExtendedAgentCard: true,
		},
		DefaultInputModes:  []string{"text/plain"},
		DefaultOutputModes: []string{"text/plain"},
		Skills: []a2a.AgentSkill{{
			ID:          "misbehave",
			Name:        "규칙 어기기",
			Description: "받은 글에 따라 규칙을 어깁니다.",
			Tags:        []string{"test"},
		}},
	}
}

// endregion

type bench struct{}

// region: execute
func (bench) Execute(
	ctx context.Context, ec *a2asrv.ExecutorContext,
) iter.Seq2[a2a.Event, error] {
	return func(yield func(a2a.Event, error) bool) {
		switch said := common.TextOf(ec.Message); said {
		case "차례 위반": // Task 를 싣기 전에 상태부터
			yield(a2a.NewStatusUpdateEvent(ec,
				a2a.TaskStateWorking, nil), nil)
		case "고장":
			yield(nil, errors.New("시험대가 고장 났습니다"))
		default:
			m := a2a.NewMessage(a2a.MessageRoleAgent,
				a2a.NewTextPart(said))
			m.ContextID = ec.ContextID
			yield(m, nil)
		}
	}
}

// endregion

func (bench) Cancel(
	ctx context.Context, ec *a2asrv.ExecutorContext,
) iter.Seq2[a2a.Event, error] {
	return common.Cancel(ec)
}

func main() {
	args := common.ParseArgs("보물상사 시험대 에이전트")
	common.Serve(card(args.URL), bench{}, args.Port, common.Options{})
}

//@ norun
