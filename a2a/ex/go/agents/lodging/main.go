// 숙소 에이전트 — 날짜·박 수·인원을 받아 가장 싼 숙소를 고른다.
//
// 보여 주는 것: 막는(blocking) SendMessage → Task, DataPart 입출력,
// INPUT_REQUIRED 로 되묻기(같은 taskId 로 이어 말하기), REJECTED.
package main

import (
	"context"
	"fmt"
	"iter"
	"maps"
	"regexp"

	"github.com/a2aproject/a2a-go/v2/a2a"
	"github.com/a2aproject/a2a-go/v2/a2asrv"

	"example.com/workshop/agents/common"
	"example.com/workshop/workshop"
)

// region: questions
// 빠진 항목을 하나씩 되묻는다. 순서가 곧 묻는 순서다.
var order = []string{"date", "nights", "headcount"}
var questions = map[string]string{
	"date":      "날짜는 언제입니까? (예: 2026-10-30)",
	"nights":    "며칠 묵습니까? (예: 1박)",
	"headcount": "인원은 몇 명입니까?",
}

// endregion

// region: card
func card(url string) *a2a.AgentCard {
	return &a2a.AgentCard{
		Name:        "보물상사 숙소 에이전트",
		Description: "날짜·박 수·인원으로 가장 싼 숙소를 고릅니다.",

		Version:             "1.0.0",
		Provider:            common.Provider,
		SupportedInterfaces: common.JSONRPCInterface(url),
		Capabilities:        a2a.AgentCapabilities{Streaming: true},
		DefaultInputModes: []string{
			"application/json", "text/plain",
		},
		DefaultOutputModes: []string{"application/json"},
		Skills: []a2a.AgentSkill{{
			ID:          "find-lodging",
			Name:        "숙소 찾기",
			Description: "워크숍 숙소를 고르고 견적을 냅니다.",
			Tags:        []string{"lodging", "workshop"},
			Examples: []string{
				`{"date":"2026-10-30","nights":1,"headcount":30}`,
			},
		}},
	}
}

// endregion

// region: from_text
// fromText 는 되물음에 글로 답한 경우('30명')를 DataPart 처럼 바꾼다.
func fromText(text string) map[string]any {
	found := map[string]any{}
	for key, rx := range map[string]*regexp.Regexp{
		"date":      workshop.ReDate,
		"nights":    workshop.ReNights,
		"headcount": workshop.ReHeadcount,
	} {
		if m := rx.FindStringSubmatch(text); m != nil {
			found[key] = m[1]
		}
	}
	return found
}

// endregion

// region: executor
type executor struct{}

func (executor) Execute(
	ctx context.Context, ec *a2asrv.ExecutorContext,
) iter.Seq2[a2a.Event, error] {
	return func(yield func(a2a.Event, error) bool) {
		task, up, ok := common.Begin(ec, yield)
		if !ok {
			return
		}
		// 사용자가 한 말만 듣는다 — 이력에는 에이전트가 되물은 말도
		// 있고, 그 예시("예: 2026-10-30")를 답으로 읽으면 안 된다.
		// Begin 이 이번 메시지까지 이력에 넣어 둔다.
		var heard []*a2a.Message
		for _, m := range task.History {
			if m.Role == a2a.MessageRoleUser {
				heard = append(heard, m)
			}
		}
		req := common.DataOf(heard...)
		for _, m := range heard {
			maps.Copy(req, fromText(common.TextOf(m)))
		}
		var missing []string
		for _, k := range order {
			if _, ok := req[k]; !ok {
				missing = append(missing, k)
			}
		}
		if len(missing) > 0 {
			common.Say("[숙소] 되묻기: %s", common.PyList(missing))
			up.Status(a2a.TaskStateInputRequired,
				common.TextPart(questions[missing[0]]),
				common.DataPart(map[string]any{"missing": missing}))
			return
		}
		// endregion

		// region: quote
		date, _ := req["date"].(string)
		quote, fail := workshop.ChooseLodging(workshop.LodgingRequest{
			Date:      date,
			Nights:    common.Int(req["nights"]),
			Headcount: common.Int(req["headcount"]),
		})
		if fail != nil {
			common.Say("[숙소] 거절: %s", fail.Reason)
			up.Status(a2a.TaskStateRejected,
				common.TextPart(fail.Reason))
			return
		}
		summary := fmt.Sprintf("%s %d실, %s원",
			quote.VenueName, quote.Rooms, common.Comma(quote.Total))
		common.Say("[숙소] 견적: %s", summary)
		up.Artifact("숙소 견적", common.Chunk{},
			common.DataPart(quote), common.TextPart(summary))
		up.Status(a2a.TaskStateCompleted)
	}
}

// endregion

func (executor) Cancel(
	ctx context.Context, ec *a2asrv.ExecutorContext,
) iter.Seq2[a2a.Event, error] {
	return common.Cancel(ec)
}

func main() {
	args := common.ParseArgs("보물상사 숙소 에이전트")
	common.Serve(card(args.URL), executor{}, args.Port,
		common.Options{})
}
