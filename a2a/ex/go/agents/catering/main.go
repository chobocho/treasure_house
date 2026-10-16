// 식사 에이전트 — 끼니마다 메뉴를 골라 스트리밍으로 알려 준다.
//
// 보여 주는 것: SendStreamingMessage(SSE), 끼니마다 WORKING 상태 갱신,
// 식단표 아티팩트를 청크로 이어 붙이기(append·lastChunk), 파일 파트
// (menu.md, raw)와 데이터 파트(견적)를 함께 돌려주기.
package main

import (
	"context"
	"flag"
	"fmt"
	"iter"
	"strings"

	"github.com/a2aproject/a2a-go/v2/a2a"
	"github.com/a2aproject/a2a-go/v2/a2asrv"

	"example.com/workshop/agents/common"
	"example.com/workshop/workshop"
)

// 끼니 이름표. 슬롯 이름(day1-dinner)을 사람이 읽는 말로 바꾼다.
var kind = map[string]string{
	"dinner": "저녁", "breakfast": "아침", "lunch": "점심",
}

func card(url string) *a2a.AgentCard {
	return &a2a.AgentCard{
		Name:        "보물상사 식사 에이전트",
		Description: "박 수·인원·채식 인원으로 끼니별 식단을 짭니다.",

		Version:             "1.0.0",
		Provider:            common.Provider,
		SupportedInterfaces: common.JSONRPCInterface(url),
		Capabilities:        a2a.AgentCapabilities{Streaming: true},
		DefaultInputModes:   []string{"application/json"},
		DefaultOutputModes: []string{
			"application/json", "text/markdown",
		},
		Skills: []a2a.AgentSkill{{
			ID:          "plan-meals",
			Name:        "식단 짜기",
			Description: "끼니마다 일반식·채식 메뉴를 고릅니다.",
			Tags:        []string{"meals", "workshop"},
			Examples: []string{
				`{"nights":1,"headcount":30,"vegetarians":2}`,
			},
		}},
	}
}

// label: day1-dinner → 1일차 저녁
func label(slot string) string {
	day, k, _ := strings.Cut(slot, "-")
	return strings.TrimPrefix(day, "day") + "일차 " + kind[k]
}

// line 은 식단표의 한 줄: 1일차 저녁: 한정식 28명, 버섯 전골 2명
func line(row workshop.Slot) string {
	var picks []string
	for _, c := range []*workshop.Choice{row.Regular, row.Vegetarian} {
		if c != nil {
			pick := fmt.Sprintf("%s %d명", c.Name, c.Count)
			picks = append(picks, pick)
		}
	}
	return label(row.Slot) + ": " + strings.Join(picks, ", ")
}

type executor struct {
	stepMs int // 끼니 사이 쉬는 시간(보여 주기용)
}

func (e executor) Execute(
	ctx context.Context, ec *a2asrv.ExecutorContext,
) iter.Seq2[a2a.Event, error] {
	return func(yield func(a2a.Event, error) bool) {
		_, up, ok := common.Begin(ec, yield)
		if !ok {
			return
		}
		req := common.DataOf(ec.Message)
		caps := map[string]int{}
		if m, ok := req["caps"].(map[string]any); ok {
			for k, v := range m {
				caps[k] = common.Int(v)
			}
		}
		plan, fail := workshop.PlanMeals(workshop.MealsRequest{
			Nights:      common.Int(req["nights"]),
			Headcount:   common.Int(req["headcount"]),
			Vegetarians: common.Int(req["vegetarians"]), // 없으면 0
			Caps:        caps,
		})
		if fail != nil {
			common.Say("[식사] 거절: %s", fail.Reason)
			up.Status(a2a.TaskStateRejected,
				common.TextPart(fail.Reason))
			return
		}
		rows := plan.Slots
		for i, row := range rows {
			if !common.Sleep(ctx, e.stepMs) {
				return
			}
			note := fmt.Sprintf("식단 짜는 중 %d/%d", i+1, len(rows))
			up.Status(a2a.TaskStateWorking, common.TextPart(note))
			// 같은 artifactId 로 한 줄씩 이어 붙인다.
			up.Artifact("식단표", common.Chunk{
				ID:     "meal-plan",
				Append: i > 0,
				Last:   i == len(rows)-1,
			}, common.TextPart(line(row)+"\n"))
		}
		var menu strings.Builder
		menu.WriteString("# 식단표\n\n")
		for _, r := range rows {
			menu.WriteString("- " + line(r) + "\n")
		}
		file := &a2a.Part{
			Content:   a2a.Raw(menu.String()),
			MediaType: "text/markdown",
			Filename:  "menu.md",
		}
		up.Artifact("식단표 파일", common.Chunk{ID: "menu-file"}, file)
		up.Artifact("식사 견적", common.Chunk{ID: "meal-quote"},
			common.DataPart(plan))
		common.Say("[식사] 견적: %s원", common.Comma(plan.Total))
		up.Status(a2a.TaskStateCompleted)
	}
}

func (executor) Cancel(
	ctx context.Context, ec *a2asrv.ExecutorContext,
) iter.Seq2[a2a.Event, error] {
	return common.Cancel(ec)
}

func main() {
	step := flag.Int("step-ms", 100, "끼니 사이 쉬는 시간(ms)")
	args := common.ParseArgs("보물상사 식사 에이전트")
	common.Serve(card(args.URL), executor{*step}, args.Port,
		common.Options{})
}
