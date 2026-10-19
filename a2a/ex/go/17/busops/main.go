// 교통 에이전트에 요청 로그·카드 캐시 머리글·본문 한도를 달아 띄운다.
//
//	go run ./17/busops --port P [--step-ms N] [--url U] [--sdk]
//	    [--cache-age 초] [--limit 바이트]
//
// agents/bus 는 main 패키지라 가져다 쓸 수 없어, 실행기와 카드를
// 그대로 옮겨 왔다(17/busstore 와 같은 사본). --sdk 는 SDK 가 주는
// 로깅 가로채기와 slog JSON 기록도 표준 출력으로 켠다.
package main

import (
	"context"
	"flag"
	"fmt"
	"iter"
	"log/slog"
	"net/http"
	"os"
	"strings"

	"github.com/a2aproject/a2a-go/v2/a2a"
	"github.com/a2aproject/a2a-go/v2/a2asrv"

	"example.com/workshop/17/deploy"
	"example.com/workshop/17/jsonlog"
	"example.com/workshop/agents/common"
	"example.com/workshop/workshop"
)

func card(url string) *a2a.AgentCard {
	return &a2a.AgentCard{
		Name:                "보물상사 교통 에이전트",
		Description:         "인원과 박 수로 버스를 고르고 배차합니다.",
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

type executor struct{ stepMs int }

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
			up.Status(a2a.TaskStateRejected,
				common.TextPart(fail.Reason))
			return
		}
		for _, step := range workshop.Workshop().BusSteps {
			if !common.Sleep(ctx, e.stepMs) {
				return // 취소되면 끝
			}
			common.Say("[교통] %s", step)
			up.Status(a2a.TaskStateWorking, common.TextPart(step))
		}
		seats := map[string]int{}
		for _, b := range workshop.Workshop().Buses {
			seats[b.ID] = b.Seats
		}
		var cars []string
		for _, v := range plan.Vehicles {
			cars = append(cars,
				fmt.Sprintf("%d인승 %d대", seats[v.ID], v.Count))
		}
		depart, _ := req["depart"].(string)
		if depart == "" {
			depart = "미정"
		}
		summary := fmt.Sprintf("%s, %d일, %s원, 출발 %s",
			strings.Join(cars, ", "), plan.Days,
			common.Comma(plan.Total), depart)
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
func main() {
	step := flag.Int("step-ms", 300, "배차 단계 하나의 시간(ms)")
	sdk := flag.Bool("sdk", false, "SDK 의 로깅 가로채기도 켠다")
	age := flag.Int("cache-age", 0, "카드의 max-age(초), 0 이면 끈다")
	limit := flag.Int64("limit", 0, "본문 한도(바이트), 0 이면 끈다")
	args := common.ParseArgs("로그·캐시·한도를 단 교통 에이전트")
	c := card(args.URL)
	// region: wire
	opts := []a2asrv.RequestHandlerOption{
		a2asrv.WithCallInterceptors(jsonlog.Interceptor{}),
	}
	if *sdk {
		// region: sdk
		h := slog.NewJSONHandler(os.Stdout, &slog.HandlerOptions{
			ReplaceAttr: shortDuration,
		})
		opts = append(opts,
			a2asrv.WithLogger(slog.New(h)),
			a2asrv.WithCallInterceptors(
				a2asrv.NewLoggingInterceptor(nil)))
		// endregion
	}
	o := common.Options{Handler: opts}
	// JSON-RPC 경로 앞에 서는 HTTP 층(카드 경로는 빠진다)
	o.Guard = func(next http.Handler) http.Handler {
		next = jsonlog.Middleware("bus", next)
		// region: deploy
		if *limit > 0 { // 로그보다 바깥 — 넘친 요청도 한 줄 남는다
			next = deploy.Limit(*limit, next)
		}
		// endregion
		return next
	}
	// endregion
	// region: card
	if *age > 0 { // SDK 의 카드 처리기를 감싼다
		sdkCard := a2asrv.NewStaticAgentCardHandler(c)
		o.Card = deploy.CardCache(*age, sdkCard)
	}
	// endregion
	common.Serve(c, executor{*step}, args.Port, o)
}

// shortDuration 은 SDK 가 나노초 정수로 적는 duration_ns 를 "1.2ms"
// 꼴 글자로 바꾼다(캡처에서는 <ms> 로 바뀐다).
func shortDuration(_ []string, a slog.Attr) slog.Attr {
	if a.Key == "duration_ns" {
		ms := float64(a.Value.Duration().Microseconds()) / 1000
		return slog.String(a.Key, fmt.Sprintf("%.1fms", ms))
	}
	return a
}

//@ norun
