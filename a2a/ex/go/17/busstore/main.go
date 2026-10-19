// 교통 에이전트를 파일 저장소로 띄운다.
//
//	go run ./17/busstore --port P [--step-ms N] [--dir D] [--recover]
//
// --dir 을 주지 않으면 $TMPDIR/tasks-P (실행 명세마다 새로 비는 곳).
// agents/bus 는 main 패키지라 가져다 쓸 수 없어, 실행기와 카드를
// 그대로 옮겨 왔다(같은 세 단계).
package main

import (
	"context"
	"flag"
	"fmt"
	"iter"
	"os"
	"path/filepath"
	"strings"

	"github.com/a2aproject/a2a-go/v2/a2a"
	"github.com/a2aproject/a2a-go/v2/a2asrv"
	"github.com/a2aproject/a2a-go/v2/a2asrv/push"

	"example.com/workshop/17/filestore"
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
	dir := flag.String("dir", "", "Task 를 둘 디렉터리")
	rec := flag.Bool("recover", false, "띄울 때 끊긴 작업을 닫는다")
	args := common.ParseArgs("파일 저장소를 쓰는 교통 에이전트")
	if *dir == "" {
		*dir = filepath.Join(os.TempDir(),
			fmt.Sprintf("tasks-%d", args.Port))
	}
	// region: wire
	store, err := filestore.New(*dir) // Task 만 디스크로
	if err == nil && *rec {
		err = store.Recover()
	}
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	// 푸시 설정은 메모리 그대로(보내기는 SDK 기본, 루프백은 막힌다)
	pushes := push.NewInMemoryStore()
	common.Serve(card(args.URL), executor{*step}, args.Port,
		common.Options{Handler: []a2asrv.RequestHandlerOption{
			a2asrv.WithTaskStore(store), // 메모리 저장소를 갈아 끼운다
			a2asrv.WithPushNotifications(pushes,
				push.NewHTTPPushSender(nil)),
		}})
	// endregion
}

//@ norun
