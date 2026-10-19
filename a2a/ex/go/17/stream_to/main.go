// 스트림에 시간 제한 1.5초 — http.Client.Timeout 은 본문 읽기까지
// 잰다(요청 전체의 제한).
//
//	go run ./17/stream_to 카드주소
package main

import (
	"context"
	"fmt"
	"net/http"
	"os"
	"strings"
	"time"

	"github.com/a2aproject/a2a-go/v2/a2a"
	"github.com/a2aproject/a2a-go/v2/a2aclient"
	"github.com/a2aproject/a2a-go/v2/a2aclient/agentcard"
)

var bus = map[string]any{
	"headcount": 30, "nights": 1, "depart": "강남역",
}

func name(s a2a.TaskState) string {
	return strings.TrimPrefix(string(s), "TASK_STATE_")
}

func show(ev a2a.Event) string {
	switch e := ev.(type) {
	case *a2a.Task:
		return "Task " + name(e.Status.State)
	case *a2a.TaskStatusUpdateEvent:
		said := []string{"상태", name(e.Status.State)}
		if m := e.Status.Message; m != nil { // 끝 상태엔 말이 없다
			for _, p := range m.Parts {
				said = append(said, p.Text())
			}
		}
		return strings.Join(said, " ")
	case *a2a.TaskArtifactUpdateEvent:
		return "아티팩트 " + e.Artifact.Name
	}
	return "?"
}

func check(err error) {
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

// region: main
func main() {
	ctx := context.Background()
	card, err := agentcard.NewResolver(http.DefaultClient).
		Resolve(ctx, os.Args[1])
	check(err)
	// region: limit
	// 클라이언트 전체의 제한 — SDK 기본은 3분
	hc := &http.Client{Timeout: 1500 * time.Millisecond}
	c, err := a2aclient.NewFromCard(ctx, card,
		a2aclient.WithJSONRPCTransport(hc))
	// endregion
	check(err)
	msg := a2a.NewMessage(a2a.MessageRoleUser, a2a.NewDataPart(bus))
	msg.ID = "m-stream"
	var id a2a.TaskID
	req := &a2a.SendMessageRequest{Message: msg}
	end := "스트림 끝"
	for ev, err := range c.SendStreamingMessage(ctx, req) {
		if err != nil {
			end = fmt.Sprint("시간 초과 → ", err)
			break
		}
		fmt.Println("  ", show(ev))
		if t, ok := ev.(*a2a.Task); ok {
			id = t.ID
		}
	}
	fmt.Println(end)
	time.Sleep(3 * time.Second) // 서버의 세 단계가 다 지나도록
	task, err := c.GetTask(ctx, &a2a.GetTaskRequest{ID: id})
	check(err)
	fmt.Println("3초 뒤 GetTask →", name(task.Status.State))
}

// endregion

//@ norun
