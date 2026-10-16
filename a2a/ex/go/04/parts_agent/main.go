// 받은 파트를 하나씩 말해 주는 에이전트 — 대답은 Task 가 아니라
// Message 하나다. 4부에서 파트의 모양과 수의 타입을 보는 실험용.
package main

import (
	"context"
	"fmt"
	"iter"
	"maps"
	"slices"
	"strings"

	"github.com/a2aproject/a2a-go/v2/a2a"
	"github.com/a2aproject/a2a-go/v2/a2asrv"

	"example.com/workshop/agents/common"
)

func card(url string) *a2a.AgentCard {
	return &a2a.AgentCard{
		Name:                "보물상사 파트 확인 에이전트",
		Description:         "받은 파트를 하나씩 말해 줍니다.",
		Version:             "1.0.0",
		SupportedInterfaces: common.JSONRPCInterface(url),
		Capabilities:        a2a.AgentCapabilities{},
		DefaultInputModes: []string{
			"text/plain", "application/json",
		},
		DefaultOutputModes: []string{"text/plain"},
		Skills: []a2a.AgentSkill{{
			ID:          "echo-parts",
			Name:        "파트 확인",
			Description: "받은 파트의 종류와 값을 돌려줍니다.",
			Tags:        []string{"debug"},
		}},
	}
}

// region: describe
// value 는 값 하나: 이 언어가 읽은 타입 이름과 값.
func value(v any) string { return fmt.Sprintf("%T %#v", v, v) }

func describe(i int, p *a2a.Part) string {
	var line string
	switch c := p.Content.(type) { // 종류는 Content 의 타입
	case a2a.Text:
		line = fmt.Sprintf("%d. text %q", i, string(c))
	case a2a.Raw:
		line = fmt.Sprintf("%d. raw %d바이트", i, len(c))
	case a2a.URL:
		line = fmt.Sprintf("%d. url %s", i, c)
	case a2a.Data:
		if m, ok := c.Value.(map[string]any); ok {
			var kv []string
			for _, k := range slices.Sorted(maps.Keys(m)) {
				kv = append(kv, k+": "+value(m[k]))
			}
			line = fmt.Sprintf("%d. data {%s}", i,
				strings.Join(kv, ", "))
		} else {
			line = fmt.Sprintf("%d. data %s", i, value(c.Value))
		}
	default: // Content 가 비었다 — 내용 필드가 하나도 없는 파트
		line = fmt.Sprintf("%d. (내용 없음)", i)
	}
	if p.Filename != "" {
		line += " filename=" + p.Filename
	}
	if p.MediaType != "" {
		line += " mediaType=" + p.MediaType
	}
	return line
}

// endregion

type echoParts struct{}

// region: execute
func (echoParts) Execute(
	ctx context.Context, ec *a2asrv.ExecutorContext,
) iter.Seq2[a2a.Event, error] {
	return func(yield func(a2a.Event, error) bool) {
		var lines []string
		for i, p := range ec.Message.Parts {
			lines = append(lines, describe(i+1, p))
		}
		fmt.Println("[파트]", strings.Join(lines, " / "))
		// Task 를 만들지 않고 Message 하나로 답한다(한 줄에 파트 하나)
		var parts []*a2a.Part
		for _, t := range lines {
			parts = append(parts, a2a.NewTextPart(t))
		}
		m := a2a.NewMessage(a2a.MessageRoleAgent, parts...)
		m.ContextID = ec.ContextID
		yield(m, nil)
	}
}

// endregion

func (echoParts) Cancel(
	ctx context.Context, ec *a2asrv.ExecutorContext,
) iter.Seq2[a2a.Event, error] {
	return common.Cancel(ec)
}

func main() {
	args := common.ParseArgs("보물상사 파트 확인 에이전트")
	common.Serve(card(args.URL), echoParts{}, args.Port, common.Options{})
}

//@ norun
