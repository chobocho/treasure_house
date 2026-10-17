// 요청 처리기를 HTTP 없이 직접 부른다 — 처리기가 하는 일만 떼어 보기.
//
//	go run ./09/direct
package main

import (
	"context"
	"fmt"
	"time"

	"github.com/a2aproject/a2a-go/v2/a2a"
	"github.com/a2aproject/a2a-go/v2/a2asrv"

	"example.com/workshop/09/steps"
)

func request(n int, now bool) *a2a.SendMessageRequest {
	data := map[string]any{
		"date": "2026-10-30", "nights": 1, "headcount": n,
	}
	msg := a2a.NewMessage(a2a.MessageRoleUser, a2a.NewDataPart(data))
	return &a2a.SendMessageRequest{Message: msg,
		Config: &a2a.SendMessageConfig{ReturnImmediately: now}}
}

func show(label string, t *a2a.Task) {
	fmt.Printf("%s: %s 이력 %d 아티팩트 %d\n", label, t.Status.State,
		len(t.History), len(t.Artifacts))
}

func main() {
	// region: handler
	card := steps.QuoteCard("http://127.0.0.1:10900/")
	handler := a2asrv.NewHandler(steps.Quote{},
		a2asrv.WithCapabilityChecks(&card.Capabilities)) // 스트림 없음
	ctx := context.Background() // 호출 맥락은 처리기가 붙인다(익명)
	// endregion

	// region: calls
	res, _ := handler.SendMessage(ctx, request(30, false))
	task := res.(*a2a.Task)
	show("SendMessage (막는 호출)", task)
	got, _ := handler.GetTask(ctx, &a2a.GetTaskRequest{ID: task.ID})
	show("GetTask", got)
	res, _ = handler.SendMessage(ctx, request(20, true))
	show("SendMessage (곧바로)", res.(*a2a.Task))
	time.Sleep(100 * time.Millisecond) // 실행기는 뒤에서 마저 돈다
	id := res.(*a2a.Task).ID
	got, _ = handler.GetTask(ctx, &a2a.GetTaskRequest{ID: id})
	show("0.1초 뒤 GetTask", got)
	_, err := handler.ListTasks(ctx, &a2a.ListTasksRequest{})
	fmt.Println("ListTasks:", err)
	for _, err := range handler.SendStreamingMessage(ctx,
		request(30, false)) {
		fmt.Println("스트림:", err)
	}
	// endregion
}
