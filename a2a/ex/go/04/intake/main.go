// 접수 에이전트 — 카드의 입력 모드 밖의 미디어 타입은 거절하고(5장),
// 인원("30명")이 없으면 되묻는다(6장의 작업 만들기용).
// Go SDK 에는 미디어 타입 검사가 없어서 실행기가 직접 대 본다.
package main

import (
	"context"
	"fmt"
	"iter"
	"log"
	"regexp"
	"slices"

	"github.com/a2aproject/a2a-go/v2/a2a"
	"github.com/a2aproject/a2a-go/v2/a2asrv"

	"example.com/workshop/agents/common"
)

var inputModes = []string{"text/plain", "application/json"}
var headcount = regexp.MustCompile(`(\d+)명`)

func card(url string) *a2a.AgentCard {
	return &a2a.AgentCard{
		Name:                "보물상사 접수 에이전트",
		Description:         "글과 JSON 만 받습니다.",
		Version:             "1.0.0",
		SupportedInterfaces: common.JSONRPCInterface(url),
		DefaultInputModes:   inputModes,
		DefaultOutputModes:  []string{"text/plain"},
		Skills: []a2a.AgentSkill{{
			ID: "intake", Name: "접수", Tags: []string{"debug"},
		}},
	}
}

type intake struct{}

func (intake) Execute(
	ctx context.Context, ec *a2asrv.ExecutorContext,
) iter.Seq2[a2a.Event, error] {
	return func(yield func(a2a.Event, error) bool) {
		// region: strict
		for _, p := range ec.Message.Parts {
			mt := p.MediaType
			if mt != "" && !slices.Contains(inputModes, mt) {
				yield(nil, fmt.Errorf("media type %s: %w",
					mt, a2a.ErrUnsupportedContentType))
				return
			}
		}
		// endregion
		_, up, ok := common.Begin(ec, yield)
		if !ok {
			return
		}
		m := headcount.FindStringSubmatch(common.TextOf(ec.Message))
		if m == nil {
			common.Say("[접수] 되묻기")
			up.Status(a2a.TaskStateInputRequired,
				common.TextPart("인원은 몇 명입니까?"))
			return
		}
		common.Say("[접수] %s명", m[1])
		up.Artifact("접수증", common.Chunk{},
			common.TextPart(m[1]+"명 접수했습니다"))
		up.Status(a2a.TaskStateCompleted)
	}
}

func (intake) Cancel(
	ctx context.Context, ec *a2asrv.ExecutorContext,
) iter.Seq2[a2a.Event, error] {
	return common.Cancel(ec)
}

func main() {
	// SDK 의 slog 기록(표준 오류)에서 날짜·시각을 뺀다 — 캡처는 실행마다
	// 같아야 하는데, 이 꼴(2026/10/16 12:00:00)은 정규화되지 않는다.
	log.SetFlags(0)
	args := common.ParseArgs("보물상사 접수 에이전트")
	common.Serve(card(args.URL), intake{}, args.Port, common.Options{})
}

//@ norun
