// Package steps 는 9부 단계 에이전트의 실행기다. 서버(step1_echo,
// step2_task)와 서버 없이 돌리는 drive 가 함께 쓰려고 패키지로 둔다.
package steps

import (
	"context"
	"iter"
	"strings"

	"github.com/a2aproject/a2a-go/v2/a2a"
	"github.com/a2aproject/a2a-go/v2/a2asrv"
)

// Echo 는 1단계 — 받은 글에 "받은 말:" 을 붙여 Message 하나로 답한다.
type Echo struct{}

// region: echo
func (Echo) Execute(
	ctx context.Context, ec *a2asrv.ExecutorContext,
) iter.Seq2[a2a.Event, error] {
	return func(yield func(a2a.Event, error) bool) {
		var words []string
		for _, p := range ec.Message.Parts {
			if t := p.Text(); t != "" {
				words = append(words, t)
			}
		}
		text := "받은 말: " + strings.Join(words, " ")
		reply := a2a.NewMessage(a2a.MessageRoleAgent,
			a2a.NewTextPart(text))
		reply.ContextID = ec.ContextID // 같은 맥락으로 답한다
		yield(reply, nil)              // 하나 내고 끝
	}
}

// Cancel — 취소할 작업이 없다. 오류 하나를 내놓는다.
func (Echo) Cancel(
	ctx context.Context, ec *a2asrv.ExecutorContext,
) iter.Seq2[a2a.Event, error] {
	return func(yield func(a2a.Event, error) bool) {
		yield(nil, a2a.ErrUnsupportedOperation)
	}
}

// endregion

// EchoCard 는 메아리 에이전트의 카드다. url 은 바깥에서 닿는 주소.
func EchoCard(url string) *a2a.AgentCard {
	return &a2a.AgentCard{
		Name:        "보물상사 메아리 에이전트",
		Description: "받은 말을 그대로 돌려줍니다.",
		Version:     "0.1.0",
		SupportedInterfaces: []*a2a.AgentInterface{
			a2a.NewAgentInterface(url, a2a.TransportProtocolJSONRPC),
		},
		DefaultInputModes:  []string{"text/plain"},
		DefaultOutputModes: []string{"text/plain"},
		Skills: []a2a.AgentSkill{{
			ID: "echo", Name: "메아리", Tags: []string{"echo"},
			Description: "받은 글 앞에 '받은 말:' 을 붙입니다.",
		}},
	}
}
