// 기능(capabilities)을 하나도 켜지 않은 에이전트 — 인사만 한다.
// 카드에 없는 기능을 부르면 서버가 무엇을 돌려주는지 보는 실험용.
//
//	--no-checks  SDK 에 카드의 기능을 넘기지 않는다(검사 끄기)
package main

import (
	"context"
	"flag"
	"iter"

	"github.com/a2aproject/a2a-go/v2/a2a"
	"github.com/a2aproject/a2a-go/v2/a2asrv"

	"example.com/workshop/agents/common"
)

// region: card
func card(url string) *a2a.AgentCard {
	return &a2a.AgentCard{
		Name:                "보물상사 안내 에이전트",
		Description:         "인사만 합니다. 켜 둔 기능이 없습니다.",
		Version:             "1.0.0",
		SupportedInterfaces: common.JSONRPCInterface(url),
		// 아무것도 켜지 않는다
		Capabilities:       a2a.AgentCapabilities{},
		DefaultInputModes:  []string{"text/plain"},
		DefaultOutputModes: []string{"text/plain"},
		Skills: []a2a.AgentSkill{{
			ID:          "greet",
			Name:        "인사",
			Description: "인사를 돌려줍니다.",
			Tags:        []string{"greeting"},
		}},
	}
}

// endregion

type greeter struct{}

func (greeter) Execute(
	ctx context.Context, ec *a2asrv.ExecutorContext,
) iter.Seq2[a2a.Event, error] {
	return func(yield func(a2a.Event, error) bool) {
		m := a2a.NewMessage(a2a.MessageRoleAgent,
			a2a.NewTextPart("안녕하세요, 보물상사입니다."))
		m.ContextID = ec.ContextID
		yield(m, nil)
	}
}

func (greeter) Cancel(
	ctx context.Context, ec *a2asrv.ExecutorContext,
) iter.Seq2[a2a.Event, error] {
	return common.Cancel(ec)
}

// region: main
func main() {
	noChecks := flag.Bool("no-checks", false, "기능 검사를 끈다")
	args := common.ParseArgs("보물상사 안내 에이전트")
	var o common.Options
	if *noChecks {
		// common.Serve 가 먼저 단 WithCapabilityChecks(&카드의 기능)
		// 를 nil 로 덮는다 — 옵션은 차례대로 적용된다.
		o.Handler = append(o.Handler, a2asrv.WithCapabilityChecks(nil))
	}
	common.Serve(card(args.URL), greeter{}, args.Port, o)
}

// endregion
//@ norun
