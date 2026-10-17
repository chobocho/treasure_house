// 실행기를 서버 없이 돌린다 — 반복자의 이벤트를 받아 찍기만 한다.
//
//	go run ./09/drive echo '숙소 부탁합니다'
//	go run ./09/drive quote 2026-10-30 1 30
//	go run ./09/drive -first 2 quote 2026-10-30 1 30
package main

import (
	"context"
	"flag"
	"fmt"
	"iter"
	"strconv"
	"strings"

	"github.com/a2aproject/a2a-go/v2/a2a"
	"github.com/a2aproject/a2a-go/v2/a2asrv"

	"example.com/workshop/09/steps"
)

func describe(ev a2a.Event) string {
	switch ev := ev.(type) {
	case *a2a.Message:
		return "Message: " + ev.Parts[0].Text()
	case *a2a.Task:
		return fmt.Sprintf("Task %s 이력 %d", ev.ID, len(ev.History))
	case *a2a.TaskStatusUpdateEvent:
		s := "상태 " + string(ev.Status.State)
		if m := ev.Status.Message; m != nil {
			s += " " + m.Parts[0].Text()
		}
		return s
	case *a2a.TaskArtifactUpdateEvent:
		q, _ := ev.Artifact.Parts[0].Data().(map[string]any)
		return fmt.Sprint("아티팩트 ", ev.Artifact.Name, ": ",
			q["venueName"])
	}
	return fmt.Sprintf("%T", ev)
}

// region: context
// ExecutorContext 는 보통 구조체 — 처리기가 하던 일을 손으로 한다
func contextFor(args []string) *a2asrv.ExecutorContext {
	part := a2a.NewTextPart(strings.Join(args, " "))
	if len(args) == 3 {
		nights, _ := strconv.Atoi(args[1])
		n, _ := strconv.Atoi(args[2])
		part = a2a.NewDataPart(map[string]any{
			"date": args[0], "nights": float64(nights),
			"headcount": float64(n), // 와이어에서 온 것처럼
		})
	}
	ec := &a2asrv.ExecutorContext{
		Message: a2a.NewMessage(a2a.MessageRoleUser, part),
		TaskID:  a2a.NewTaskID(), ContextID: a2a.NewContextID(),
	}
	fmt.Println("taskId   ", ec.TaskID)
	fmt.Println("contextId", ec.ContextID)
	fmt.Printf("메시지의 taskId: %q\n", ec.Message.TaskID)
	fmt.Println("이어 말하기?", ec.StoredTask != nil)
	return ec
}

// endregion

// region: careless
// careless 는 yield 의 답을 보지 않는 실행기 — 하면 안 되는 예
var careless = a2asrv.AgentExecutorFunc(func(
	ctx context.Context, ec *a2asrv.ExecutorContext,
) iter.Seq2[a2a.Event, error] {
	return func(yield func(a2a.Event, error) bool) {
		yield(a2a.NewSubmittedTask(ec, ec.Message), nil)
		yield(a2a.NewStatusUpdateEvent(ec,
			a2a.TaskStateWorking, nil), nil) // false 를 버렸다
		yield(a2a.NewStatusUpdateEvent(ec,
			a2a.TaskStateCompleted, nil), nil)
	}
})

// endregion

func main() {
	first := flag.Int("first", 0, "이벤트 N 개만 받고 그만둔다")
	flag.Parse()
	defer func() { // 반복자 규칙을 어기면 런타임이 panic 을 낸다
		if r := recover(); r != nil {
			fmt.Println("  ✗ panic:", r)
		}
	}()
	exec := map[string]a2asrv.AgentExecutor{
		"echo": steps.Echo{}, "quote": steps.Quote{},
		"careless": careless,
	}[flag.Arg(0)]
	ec := contextFor(flag.Args()[1:])
	// region: range
	// 실행기가 돌려준 반복자를 range 로 돈다 — 그것이 전부다
	n := 0
	for ev, err := range exec.Execute(context.Background(), ec) {
		if err != nil {
			fmt.Println("  ✗", err)
			break
		}
		fmt.Println("  →", describe(ev))
		if n++; n == *first {
			fmt.Println("  (그만 받는다 — yield 가 false 를 돌려준다)")
			break
		}
	}
	// endregion
}

//@ norun
