// 교통 칸의 셋째 대본 — returnImmediately 로 맡기고, GetTask 로
// WORKING 을 본 뒤 CancelTask, 한 단계 넘게 기다렸다 다시 GetTask.
//
//	go run ./16/cancel 카드주소
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

func name(t *a2a.Task) string {
	return strings.TrimPrefix(string(t.Status.State), "TASK_STATE_")
}

func check(err error) {
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

func main() {
	ctx := context.Background()
	r := agentcard.NewResolver(http.DefaultClient)
	card, err := r.Resolve(ctx, os.Args[1])
	check(err)
	c, err := a2aclient.NewFromCard(ctx, card)
	check(err)
	msg := a2a.NewMessage(a2a.MessageRoleUser, a2a.NewDataPart(bus))
	msg.ID = "bus-cancel"
	res, err := c.SendMessage(ctx, &a2a.SendMessageRequest{
		Message: msg,
		Config:  &a2a.SendMessageConfig{ReturnImmediately: true},
	})
	check(err)
	task := res.(*a2a.Task)
	fmt.Println("SendMessage →", name(task))
	// region: cancel
	get := &a2a.GetTaskRequest{ID: task.ID}
	for name(task) != "WORKING" { // 첫 단계가 시작될 때까지
		time.Sleep(50 * time.Millisecond)
		task, err = c.GetTask(ctx, get)
		check(err)
	}
	fmt.Println("GetTask     →", name(task))
	task, err = c.CancelTask(ctx, &a2a.CancelTaskRequest{ID: task.ID})
	check(err)
	fmt.Println("CancelTask  →", name(task))
	time.Sleep(2500 * time.Millisecond) // 한 단계(2초)보다 길게
	task, err = c.GetTask(ctx, get)
	check(err)
	fmt.Println("GetTask     →", name(task), "아티팩트",
		len(task.Artifacts))
	// endregion
}

//@ norun
