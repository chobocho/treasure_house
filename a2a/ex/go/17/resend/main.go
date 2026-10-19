// 시간 초과 뒤 같은 messageId 로 다시 보내면 — 작업이 둘 생긴다.
//
//	go run ./17/resend 카드주소
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

// 나중에 ListTasks 로 거르려고 맥락을 정해 둔다
const ctxID = "ctx-resend"

func name(t *a2a.Task) string {
	return strings.TrimPrefix(string(t.Status.State), "TASK_STATE_")
}

func check(err error) {
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

// region: send
func send(c *a2aclient.Client, d time.Duration) (*a2a.Task, error) {
	// 이 호출만의 제한 — ctx 가 끝나면 요청도 끊긴다
	ctx, cancel := context.WithTimeout(context.Background(), d)
	defer cancel()
	msg := a2a.NewMessage(a2a.MessageRoleUser, a2a.NewDataPart(bus))
	msg.ID, msg.ContextID = "m-resend", ctxID
	req := &a2a.SendMessageRequest{Message: msg}
	res, err := c.SendMessage(ctx, req)
	if err != nil {
		return nil, err
	}
	return res.(*a2a.Task), nil
}

// endregion

func main() {
	ctx := context.Background()
	card, err := agentcard.NewResolver(http.DefaultClient).
		Resolve(ctx, os.Args[1])
	check(err)
	c, err := a2aclient.NewFromCard(ctx, card)
	check(err)
	if _, err := send(c, 1500*time.Millisecond); err != nil {
		fmt.Println("① 1.5초 제한 →", err)
	}
	task, err := send(c, 10*time.Second)
	check(err)
	fmt.Println("② 같은 messageId 로 다시 →", name(task))
	list := &a2a.ListTasksRequest{ContextID: ctxID}
	page, err := c.ListTasks(ctx, list)
	check(err)
	fmt.Printf("③ ListTasks(contextId) → %d건\n", len(page.Tasks))
	for _, t := range page.Tasks {
		fmt.Println("  ", name(t), "첫 메시지", t.History[0].ID)
	}
}

//@ norun
