package main

import (
	"context"
	"fmt"
	"iter"
	"slices"
	"strings"

	"github.com/a2aproject/a2a-go/v2/a2a"
	"github.com/a2aproject/a2a-go/v2/a2aclient"
	"github.com/a2aproject/a2a-go/v2/a2aext"
	"github.com/a2aproject/a2a-go/v2/a2asrv"
)

// Budget 은 이 책의 확장(14부)이다.
const Budget = "https://treasure-house.example/a2a/ext/budget/v1"

func serverPropagator() a2asrv.CallInterceptor {
	return a2aext.NewServerPropagator(nil) // 기본: 요청된 확장만
}

// region: relay
// relay 는 받은 말을 아래 에이전트 둘에게 넘긴다 — 카드 하나는
// Budget 확장을 적었고, 하나는 적지 않았다. 확장 머리글과 metadata
// 는 우리가 옮기지 않는다. 가로채기 짝(서버·클라이언트)이 옮긴다.
type relay struct{ down string }

func (r relay) Execute(ctx context.Context, ec *a2asrv.ExecutorContext,
) iter.Seq2[a2a.Event, error] {
	return func(yield func(a2a.Event, error) bool) {
		var heard []*a2a.Part
		budget := []a2a.AgentExtension{{URI: Budget}}
		for _, ext := range [][]a2a.AgentExtension{budget, nil} {
			card := &a2a.AgentCard{Name: "아래",
				SupportedInterfaces: []*a2a.AgentInterface{
					a2a.NewAgentInterface(r.down,
						a2a.TransportProtocolJSONRPC)},
				Capabilities: a2a.AgentCapabilities{Extensions: ext}}
			c, err := a2aclient.NewFromCard(ctx, card,
				a2aclient.WithCallInterceptors(
					a2aext.NewClientPropagator(nil)))
			if err != nil {
				yield(nil, err)
				return
			}
			m := a2a.NewMessage(a2a.MessageRoleUser,
				ec.Message.Parts...)
			res, err := c.SendMessage(ctx,
				&a2a.SendMessageRequest{Message: m})
			c.Destroy()
			if err != nil {
				yield(nil, err)
				return
			}
			heard = append(heard, res.(*a2a.Message).Parts...)
		}
		yield(a2a.NewMessage(a2a.MessageRoleAgent, heard...), nil)
	}
}

func (relay) Cancel(ctx context.Context, ec *a2asrv.ExecutorContext,
) iter.Seq2[a2a.Event, error] {
	return func(yield func(a2a.Event, error) bool) {}
}

// endregion

// who 는 아래 에이전트 — 받은 확장과 요청 metadata 의 키를 말한다.
func who(ctx context.Context, ec *a2asrv.ExecutorContext,
) iter.Seq2[a2a.Event, error] {
	return func(yield func(a2a.Event, error) bool) {
		ext, _ := a2asrv.ExtensionsFrom(ctx)
		var keys []string
		for k := range ec.Metadata {
			keys = append(keys, k)
		}
		slices.Sort(keys)
		said := fmt.Sprintf("확장=%q metadata=[%s]",
			ext.RequestedURIs(), strings.Join(keys, " "))
		yield(a2a.NewMessage(a2a.MessageRoleAgent,
			a2a.NewTextPart(said)), nil)
	}
}
