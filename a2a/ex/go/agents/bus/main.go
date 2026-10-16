// 교통 에이전트 — 버스를 고르고, 시간이 걸리는 배차를 진행한다.
//
// 보여 주는 것: returnImmediately 로 바로 돌려받는 Task, 오래 걸리는
// 작업의 단계별 상태 갱신, 푸시 알림(웹훅), GetTask 폴링, ListTasks,
// CancelTask(→ CANCELED), SubscribeToTask.
package main

import (
	"bytes"
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"iter"
	"log/slog"
	"net/http"
	"strings"
	"time"

	"github.com/a2aproject/a2a-go/v2/a2a"
	"github.com/a2aproject/a2a-go/v2/a2asrv"
	"github.com/a2aproject/a2a-go/v2/a2asrv/push"

	"example.com/workshop/agents/common"
	"example.com/workshop/workshop"
)

func card(url string) *a2a.AgentCard {
	return &a2a.AgentCard{
		Name:        "보물상사 교통 에이전트",
		Description: "인원과 박 수로 버스를 고르고 배차합니다.",

		Version:             "1.0.0",
		Provider:            common.Provider,
		SupportedInterfaces: common.JSONRPCInterface(url),
		Capabilities: a2a.AgentCapabilities{
			Streaming: true, PushNotifications: true,
		},
		DefaultInputModes:  []string{"application/json"},
		DefaultOutputModes: []string{"application/json"},
		Skills: []a2a.AgentSkill{{
			ID:          "book-bus",
			Name:        "버스 배차",
			Description: "전세 버스를 고르고 배차까지 진행합니다.",
			Tags:        []string{"transport", "workshop"},
			Examples: []string{
				`{"headcount":30,"nights":1,"depart":"강남역"}`,
			},
		}},
	}
}

// vehiclesText: [{"id":"bus45","count":1}] → 45인승 1대
func vehiclesText(plan workshop.BusPlan) string {
	seats := map[string]int{}
	for _, b := range workshop.Workshop().Buses {
		seats[b.ID] = b.Seats
	}
	var out []string
	for _, v := range plan.Vehicles {
		out = append(out,
			fmt.Sprintf("%d인승 %d대", seats[v.ID], v.Count))
	}
	return strings.Join(out, ", ")
}

type executor struct {
	stepMs int // 배차 단계 하나에 걸리는 시간
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
		plan, fail := workshop.ChooseBuses(workshop.BusRequest{
			Headcount: common.Int(req["headcount"]),
			Nights:    common.Int(req["nights"]),
		})
		if fail != nil {
			common.Say("[교통] 거절: %s", fail.Reason)
			up.Status(a2a.TaskStateRejected,
				common.TextPart(fail.Reason))
			return
		}
		for _, step := range workshop.Workshop().BusSteps {
			if !common.Sleep(ctx, e.stepMs) {
				return // 취소되면 여기서 끊긴다
			}
			common.Say("[교통] %s", step)
			up.Status(a2a.TaskStateWorking, common.TextPart(step))
		}
		depart, _ := req["depart"].(string)
		if depart == "" { // 없거나 null 이면
			depart = "미정"
		}
		summary := fmt.Sprintf("%s, %d일, %s원, 출발 %s",
			vehiclesText(plan), plan.Days, common.Comma(plan.Total),
			depart)
		up.Artifact("배차 확인서", common.Chunk{ID: "bus-booking"},
			common.DataPart(plan), common.TextPart(summary))
		common.Say("[교통] 완료: %s", summary)
		up.Status(a2a.TaskStateCompleted)
	}
}

func (executor) Cancel(
	ctx context.Context, ec *a2asrv.ExecutorContext,
) iter.Seq2[a2a.Event, error] {
	common.Say("[교통] 취소")
	return common.Cancel(ec, common.TextPart("배차를 취소했습니다"))
}

// region: push
// hookSender 는 푸시 알림을 웹훅에 POST 한다. SDK 의 HTTPPushSender
// 를 쓰지 않는 까닭 둘: 토큰 헤더 이름이 A2A-Notification-Token 으로
// 파이썬·TS 의 X-A2A-Notification-Token 과 다르고(명세는 이름을 정하지
// 않는다), 기본값이 루프백(127.0.0.1) 주소를 막는다.
type hookSender struct{ client *http.Client }

func (s hookSender) SendPush(
	ctx context.Context, cfg *a2a.PushConfig, ev a2a.Event,
) error {
	body, err := json.Marshal(a2a.StreamResponse{Event: ev})
	if err != nil {
		return err
	}
	req, err := http.NewRequestWithContext(ctx, http.MethodPost,
		cfg.URL, bytes.NewReader(body))
	if err != nil {
		return err
	}
	req.Header.Set("Content-Type", "application/json")
	if cfg.Token != "" {
		req.Header.Set("X-A2A-Notification-Token", cfg.Token)
	}
	resp, err := s.client.Do(req)
	if err != nil {
		// 웹훅이 죽어도 작업은 계속한다(오류를 돌려주면 SDK 가
		// 작업을 FAILED 로 바꾼다). 파이썬 SDK 도 기록만 남긴다.
		slog.Warn("push failed", "url", cfg.URL, "error", err)
		return nil
	}
	return resp.Body.Close()
}

// endregion

func main() {
	step := flag.Int("step-ms", 300, "배차 단계 하나의 시간(ms)")
	args := common.ParseArgs("보물상사 교통 에이전트")
	sender := hookSender{&http.Client{Timeout: 10 * time.Second}}
	common.Serve(card(args.URL), executor{*step}, args.Port,
		common.Options{Handler: []a2asrv.RequestHandlerOption{
			a2asrv.WithPushNotifications(push.NewInMemoryStore(),
				sender),
		}})
}
