// ListTasks — 작업 셋(맥락 ctx-a 에 30명·0명, ctx-b 에 70명)을 만든 뒤
// 필터·페이지·이력 길이를 바꿔 가며 목록을 받는다.
//
//	go run ./11/listing 에이전트
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
)

var jobs = []struct {
	id, ctx string
	data    map[string]any
}{
	{"list-a", "ctx-a", map[string]any{"headcount": 30, "nights": 1}},
	{"list-b", "ctx-a", map[string]any{"headcount": 0, "nights": 1}},
	{"list-c", "ctx-b", map[string]any{"headcount": 70, "nights": 2}},
}

func make3(ctx context.Context, c *a2aclient.Client) {
	for _, j := range jobs { // 막는 호출 — 끝나야 다음으로
		part := a2a.NewDataPart(j.data)
		msg := a2a.NewMessage(a2a.MessageRoleUser, part)
		msg.ID, msg.ContextID = j.id, j.ctx
		req := &a2a.SendMessageRequest{Message: msg}
		_, err := c.SendMessage(ctx, req)
		check(err)
	}
}

func row(t *a2a.Task) string {
	first := "-"
	if len(t.History) > 0 {
		first = t.History[0].ID
	}
	state := strings.TrimPrefix(string(t.Status.State), "TASK_STATE_")
	return fmt.Sprintf("%s %-9s %-6s 이력 %d 아티팩트 %d",
		t.ContextID, state, first, len(t.History), len(t.Artifacts))
}

// region: list
func show(ctx context.Context, c *a2aclient.Client, title string,
	req *a2a.ListTasksRequest) string {
	res, err := c.ListTasks(ctx, req)
	check(err)
	next := `""`
	if res.NextPageToken != "" {
		next = "있음"
	}
	fmt.Printf("%s: total %d page %d next %s\n",
		title, res.TotalSize, res.PageSize, next)
	for _, t := range res.Tasks {
		fmt.Println("  ", row(t))
	}
	return res.NextPageToken
}

func lists(ctx context.Context, c *a2aclient.Client) {
	show(ctx, c, "전부", &a2a.ListTasksRequest{})
	show(ctx, c, "contextId=ctx-a",
		&a2a.ListTasksRequest{ContextID: "ctx-a"})
	show(ctx, c, "status=COMPLETED",
		&a2a.ListTasksRequest{Status: a2a.TaskStateCompleted})
	token := "" // 한 장에 하나씩 — 토큰이 빌 때까지
	for n := 1; ; n++ {
		token = show(ctx, c, fmt.Sprintf("pageSize=1 (%d)", n),
			&a2a.ListTasksRequest{PageSize: 1, PageToken: token})
		if token == "" {
			break
		}
	}
	zero := 0
	show(ctx, c, "historyLength=0 + 아티팩트", &a2a.ListTasksRequest{
		HistoryLength: &zero, IncludeArtifacts: true})
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
	card, err := agentcard.NewResolver(http.DefaultClient).
		Resolve(ctx, os.Args[1])
	check(err)
	c, err := a2aclient.NewFromCard(ctx, card)
	check(err)
	make3(ctx, c)
	lists(ctx, c)
}

//@ norun
