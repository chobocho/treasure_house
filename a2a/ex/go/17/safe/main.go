// 끊긴 SendMessage 를 다시 보내지 않고 — 맥락으로 작업을 찾아 다시
// 붙는다.
//
//	go run ./17/safe 카드주소
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

// 보내기 전에 맥락을 정해 둔다 — 찾을 열쇠
const ctxID = "ctx-safe"

func name(s a2a.TaskState) string {
	return strings.TrimPrefix(string(s), "TASK_STATE_")
}

func stateOf(ev a2a.Event) string {
	switch e := ev.(type) {
	case *a2a.Task:
		return name(e.Status.State)
	case *a2a.TaskStatusUpdateEvent:
		return name(e.Status.State)
	}
	return fmt.Sprintf("%T", ev)
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
	c, err := a2aclient.NewFromCard(ctx, card)
	check(err)
	bus := map[string]any{
		"headcount": 30, "nights": 1, "depart": "강남역"}
	msg := a2a.NewMessage(a2a.MessageRoleUser, a2a.NewDataPart(bus))
	msg.ID, msg.ContextID = "m-safe", ctxID
	short, cancel := context.WithTimeout(ctx, 1500*time.Millisecond)
	_, err = c.SendMessage(short, &a2a.SendMessageRequest{Message: msg})
	cancel()
	if err != nil {
		fmt.Println("① 1.5초에 끊김 — 다시 보내지 않는다")
	}
	list := &a2a.ListTasksRequest{ContextID: ctxID}
	page, err := c.ListTasks(ctx, list)
	check(err)
	task := page.Tasks[0]
	fmt.Printf("② ListTasks(contextId) → %d건 %s\n",
		len(page.Tasks), name(task.Status.State))
	// region: sub
	var seen []a2a.Event
	sub := &a2a.SubscribeToTaskRequest{ID: task.ID}
	for ev, err := range c.SubscribeToTask(ctx, sub) {
		check(err)
		seen = append(seen, ev)
	}
	// endregion
	fmt.Printf("③ SubscribeToTask → 처음 %s … 끝 %s\n",
		stateOf(seen[0]), stateOf(seen[len(seen)-1]))
	page, err = c.ListTasks(ctx, list)
	check(err)
	fmt.Printf("④ ListTasks(contextId) → %d건 %s\n",
		len(page.Tasks), name(page.Tasks[0].Status.State))
}

// endregion

//@ norun
