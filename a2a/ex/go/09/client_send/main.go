// SDK 클라이언트로 숙소 견적을 묻는다 — 막는 호출과 스트림.
//
//	go run ./09/client_send [-no-stream] URL
package main

import (
	"context"
	"flag"
	"fmt"
	"os"
	"strings"

	"github.com/a2aproject/a2a-go/v2/a2a"
	"github.com/a2aproject/a2a-go/v2/a2aclient"
	"github.com/a2aproject/a2a-go/v2/a2aclient/agentcard"
)

func name(s a2a.TaskState) string {
	return strings.TrimPrefix(string(s), "TASK_STATE_")
}

// region: show
// 이벤트 하나 — 넷 중 무엇인지는 타입 스위치로 가른다
func show(ev a2a.Event) {
	switch e := ev.(type) {
	case *a2a.Task:
		fmt.Printf("  *a2a.Task %s 아티팩트 %d\n",
			name(e.Status.State), len(e.Artifacts))
	case *a2a.TaskStatusUpdateEvent:
		fmt.Printf("  *a2a.TaskStatusUpdateEvent %s\n",
			name(e.Status.State))
	case *a2a.TaskArtifactUpdateEvent:
		fmt.Printf("  *a2a.TaskArtifactUpdateEvent %s\n",
			e.Artifact.Name)
	case *a2a.Message:
		fmt.Println("  *a2a.Message")
	}
}

// endregion

// region: connect
// 카드를 받아(해석기) 클라이언트를 짓는다(팩토리) — 두 단계다
func connect(
	ctx context.Context, url string,
) (*a2aclient.Client, error) {
	card, err := agentcard.DefaultResolver.Resolve(ctx, url)
	if err != nil {
		return nil, err
	}
	return a2aclient.NewFromCard(ctx, card)
}

// endregion

// region: send
func run(ctx context.Context, url string, stream bool) error {
	client, err := connect(ctx, url)
	if err != nil {
		return err
	}
	defer client.Destroy()
	m := a2a.NewMessage(a2a.MessageRoleUser, a2a.NewDataPart(
		map[string]any{"date": "2026-10-30", "nights": 1,
			"headcount": 30}))
	m.ID = "c-1"
	req := &a2a.SendMessageRequest{Message: m}
	var id a2a.TaskID
	if stream {
		fmt.Println("스트림")
		for ev, err := range client.SendStreamingMessage(ctx, req) {
			if err != nil {
				return err
			}
			show(ev)
			if t, ok := ev.(*a2a.Task); ok {
				id = t.ID
			}
		}
	} else {
		fmt.Println("막는 호출")
		res, err := client.SendMessage(ctx, req) // Task 또는 Message
		if err != nil {
			return err
		}
		show(res)
		if t, ok := res.(*a2a.Task); ok {
			id = t.ID
		}
	}
	t, err := client.GetTask(ctx, &a2a.GetTaskRequest{ID: id})
	if err != nil {
		return err
	}
	fmt.Printf("GetTask: %s 아티팩트 %d 이력 %d\n",
		name(t.Status.State), len(t.Artifacts), len(t.History))
	return nil
}

// endregion

func main() {
	noStream := flag.Bool("no-stream", false, "막는 호출로")
	flag.Parse()
	if err := run(context.Background(), flag.Arg(0),
		!*noStream); err != nil {
		fmt.Fprintln(os.Stderr, "오류:", err)
		os.Exit(1)
	}
}

//@ norun
