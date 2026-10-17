// 3단계 — 빠진 것을 되묻는 숙소 에이전트. 결함이 하나 있다.
//
//	go run ./09/step3_ask --port P
//
// 물음 목록·fromText·카드는 agents/lodging 에서 옮겨 적었다 — 그
// 파일은 package main 이라 import 할 수 없다.
package main

import (
	"context"
	"encoding/json"
	"iter"
	"maps"
	"regexp"

	"github.com/a2aproject/a2a-go/v2/a2a"
	"github.com/a2aproject/a2a-go/v2/a2asrv"

	"example.com/workshop/agents/common"
	"example.com/workshop/workshop"
)

var order = []string{"date", "nights", "headcount"}
var questions = map[string]string{
	"date":      "날짜는 언제입니까? (예: 2026-10-30)",
	"nights":    "며칠 묵습니까? (예: 1박)",
	"headcount": "인원은 몇 명입니까?",
}

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

// region: executor
// step3 은 3단계 실행기. 8장의 시험은 같은 패키지의 main_test.go 다.
type step3 struct{}

func (step3) Execute(
	ctx context.Context, ec *a2asrv.ExecutorContext,
) iter.Seq2[a2a.Event, error] {
	return func(yield func(a2a.Event, error) bool) {
		task, up, ok := common.Begin(ec, yield) // 이력이 들어 있다
		if !ok {
			return
		}
		heard := task.History // 이것이 결함이다
		req := common.DataOf(heard...)
		for _, m := range heard {
			maps.Copy(req, fromText(common.TextOf(m)))
		}
		said, _ := json.Marshal(req)
		common.Say("[3단계] 들은 것: %s", said)
		var missing []string
		for _, k := range order {
			if _, ok := req[k]; !ok {
				missing = append(missing, k)
			}
		}
		if len(missing) > 0 { // 첫째를 글로, 빠진 목록은 데이터로
			up.Status(a2a.TaskStateInputRequired, // 멈춤
				common.TextPart(questions[missing[0]]),
				common.DataPart(map[string]any{"missing": missing}))
			return // 다음 말이 오면 처리기가 Execute 를 다시 부른다
		}
		date, _ := req["date"].(string)
		q, fail := workshop.ChooseLodging(workshop.LodgingRequest{
			Date: date, Nights: common.Int(req["nights"]),
			Headcount: common.Int(req["headcount"]),
		})
		if fail != nil {
			up.Status(a2a.TaskStateRejected,
				common.TextPart(fail.Reason))
			return
		}
		up.Artifact("숙소 견적", common.Chunk{}, common.DataPart(q))
		up.Status(a2a.TaskStateCompleted)
	}
}

// endregion

func (step3) Cancel(
	ctx context.Context, ec *a2asrv.ExecutorContext,
) iter.Seq2[a2a.Event, error] {
	return common.Cancel(ec)
}

// card 는 완성판의 카드를 옮겨 적은 것이다.
func card(url string) *a2a.AgentCard {
	return &a2a.AgentCard{
		Name:                "보물상사 숙소 에이전트 (3단계)",
		Description:         "빠진 조건을 되물어 숙소를 고릅니다.",
		Version:             "0.3.0",
		Provider:            common.Provider,
		SupportedInterfaces: common.JSONRPCInterface(url),
		Capabilities:        a2a.AgentCapabilities{Streaming: true},
		DefaultInputModes: []string{
			"application/json", "text/plain",
		},
		DefaultOutputModes: []string{"application/json"},
		Skills: []a2a.AgentSkill{{
			ID: "find-lodging", Name: "숙소 찾기",
			Description: "워크숍 숙소를 고르고 견적을 냅니다.",
			Tags:        []string{"lodging", "workshop"},
		}},
	}
}

func main() {
	args := common.ParseArgs("숙소 에이전트 3단계")
	common.Serve(card(args.URL), step3{}, args.Port, common.Options{})
}

//@ norun
