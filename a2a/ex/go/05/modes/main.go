// 교통 에이전트에 같은 배차 요청을 두 번 — 막는 호출로 한 번,
// returnImmediately 로 한 번 — 보내고, 둘째는 GetTask 로 지켜본다.
//
//	go run ./05/modes 카드주소
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

var bus = map[string]any{"headcount": 30, "nights": 1, "depart": "강남역"}

func name(t *a2a.Task) string {
	return strings.TrimPrefix(string(t.Status.State), "TASK_STATE_")
}

// region: send
func send(
	ctx context.Context, c *a2aclient.Client, id string, now bool,
) *a2a.Task {
	msg := a2a.NewMessage(a2a.MessageRoleUser, a2a.NewDataPart(bus))
	msg.ID = id
	// ReturnImmediately 는 요청의 Config 에 싣는다
	req := &a2a.SendMessageRequest{
		Message: msg,
		Config:  &a2a.SendMessageConfig{ReturnImmediately: now},
	}
	res, err := c.SendMessage(ctx, req)
	check(err)
	return res.(*a2a.Task) // 교통 에이전트는 늘 Task 로 답한다
}

// endregion

// region: poll
func poll(
	ctx context.Context, c *a2aclient.Client, id a2a.TaskID,
) *a2a.Task {
	seen := ""
	for {
		// 상태가 바뀔 때만 찍는다(몇 번 물었는지는 그때그때 다르다)
		task, err := c.GetTask(ctx, &a2a.GetTaskRequest{ID: id})
		check(err)
		if name(task) != seen {
			seen = name(task)
			fmt.Println("  GetTask →", seen)
		}
		if task.Status.State.Terminal() {
			return task
		}
		time.Sleep(100 * time.Millisecond)
	}
}

// endregion

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
	task := send(ctx, c, "bus-wait", false)
	fmt.Println("막는 호출         →", name(task), len(task.Artifacts))
	task = send(ctx, c, "bus-now", true)
	fmt.Println("returnImmediately →", name(task), len(task.Artifacts))
	task = poll(ctx, c, task.ID)
	fmt.Println("  아티팩트:", task.Artifacts[0].Name)
}

//@ norun
