// 요청 처리기를 HTTP 없이 직접 부른다 — 처리기가 하는 일만 떼어 보기.
//
//	go run ./09/direct
package main

import (
	"context"
	"fmt"
	"iter"
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

// region: held
// held 는 첫 이벤트(SUBMITTED Task)를 낸 뒤 표가 올 때까지
// 실행기를 세운다. Go 처리기는 곧바로 답할 때 그 순간 저장소의
// Task 를 읽어 준다(handler.go:313) — 세우지 않으면 SUBMITTED·
// WORKING·COMPLETED 중 무엇이 찍힐지 실행기와의 경합이다.
type held struct {
	steps.Quote
	gate chan struct{} // 실행 한 번에 표 한 장
}

func (h held) Execute(
	ctx context.Context, ec *a2asrv.ExecutorContext,
) iter.Seq2[a2a.Event, error] {
	return func(yield func(a2a.Event, error) bool) {
		first := true
		for ev, err := range h.Quote.Execute(ctx, ec) {
			if !yield(ev, err) {
				return
			}
			if first {
				first = false
				<-h.gate
			}
		}
	}
}

// endregion

func main() {
	// region: handler
	card := steps.QuoteCard("http://127.0.0.1:10900/")
	exec := held{gate: make(chan struct{}, 1)}
	handler := a2asrv.NewHandler(exec,
		a2asrv.WithCapabilityChecks(&card.Capabilities)) // 스트림 없음
	ctx := context.Background() // 호출 맥락은 처리기가 붙인다(익명)
	// endregion

	// region: calls
	exec.gate <- struct{}{} // 막는 호출은 표를 미리 쥐여 준다
	res, _ := handler.SendMessage(ctx, request(30, false))
	task := res.(*a2a.Task)
	show("SendMessage (막는 호출)", task)
	got, _ := handler.GetTask(ctx, &a2a.GetTaskRequest{ID: task.ID})
	show("GetTask", got)
	res, _ = handler.SendMessage(ctx, request(20, true))
	show("SendMessage (곧바로)", res.(*a2a.Task))
	exec.gate <- struct{}{}            // 답을 받은 뒤에야 놓아준다
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
