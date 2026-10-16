// 배차 하나를 끝까지 맡긴 뒤, 같은 작업을 historyLength 만 바꿔
// 여러 번 GetTask 한다. 이력이 몇 개, 어떤 것이 오는지 찍는다.
//
//	go run ./05/history 카드주소
package main

import (
	"context"
	"fmt"
	"net/http"
	"os"
	"strings"

	"github.com/a2aproject/a2a-go/v2/a2a"
	"github.com/a2aproject/a2a-go/v2/a2aclient"
	"github.com/a2aproject/a2a-go/v2/a2aclient/agentcard"

	"example.com/workshop/agents/common"
)

var bus = map[string]any{
	"headcount": 30, "nights": 1, "depart": "강남역",
}

func line(t *a2a.Task) string {
	said := []string{}
	for _, m := range t.History {
		if s := common.TextOf(m); s != "" {
			said = append(said, s)
		} else {
			said = append(said, "(데이터)")
		}
	}
	return strings.TrimSpace(
		fmt.Sprintf("%d개 %s", len(said), strings.Join(said, " / ")))
}

// region: history
func run(ctx context.Context, c *a2aclient.Client) {
	msg := a2a.NewMessage(a2a.MessageRoleUser, a2a.NewDataPart(bus))
	msg.ID = "bus-h"
	req := &a2a.SendMessageRequest{Message: msg}
	res, err := c.SendMessage(ctx, req) // 막는 호출 — COMPLETED
	check(err)
	id := res.(*a2a.Task).ID
	task, err := c.GetTask(ctx, &a2a.GetTaskRequest{ID: id})
	check(err)
	fmt.Println("없음 →", line(task))
	for _, n := range []int{0, 1, 2, 10, -1} {
		// HistoryLength 는 *int — nil 이면 "없음", &0 이면 "0 을 줬다"
		get := &a2a.GetTaskRequest{ID: id, HistoryLength: &n}
		if task, err := c.GetTask(ctx, get); err != nil {
			fmt.Printf("%4d → 오류 %v\n", n, err)
		} else {
			fmt.Printf("%4d → %s\n", n, line(task))
		}
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
	run(ctx, c)
}

//@ norun
