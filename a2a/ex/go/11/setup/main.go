// 교통 에이전트에 푸시 설정을 두 번 단다 — 보내는 요청에 하나(inline),
// 돌려받은 작업에 CreateTaskPushNotificationConfig 로 하나. 그다음
// 중계기(relay.py)에 무엇이 왔는지 묻는다.
//
//	go run ./11/setup 에이전트주소 웹훅주소 중계기주소
package main

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"sort"
	"strings"

	"github.com/a2aproject/a2a-go/v2/a2a"
	"github.com/a2aproject/a2a-go/v2/a2aclient"
	"github.com/a2aproject/a2a-go/v2/a2aclient/agentcard"
)

var bus = map[string]any{
	"headcount": 30, "nights": 1, "depart": "강남역",
}

var agent, hook, relay = os.Args[1], os.Args[2], os.Args[3]

// region: inline
func send(ctx context.Context, c *a2aclient.Client) *a2a.Task {
	msg := a2a.NewMessage(a2a.MessageRoleUser, a2a.NewDataPart(bus))
	msg.ID = "push-1"
	// 작업 id 는 아직 없으니 TaskID 는 비워 둔다(proto 주석)
	push := &a2a.PushConfig{URL: hook, Token: "tok-inline"}
	req := &a2a.SendMessageRequest{
		Message: msg,
		Config: &a2a.SendMessageConfig{
			ReturnImmediately: true, PushConfig: push,
		},
	}
	res, err := c.SendMessage(ctx, req)
	check(err)
	return res.(*a2a.Task)
}

// endregion

// region: create
func create(
	ctx context.Context, c *a2aclient.Client, id a2a.TaskID,
) *a2a.PushConfig {
	got, err := c.CreateTaskPushConfig(ctx, &a2a.PushConfig{
		TaskID: id, ID: "hook-2", URL: hook, Token: "tok-create",
	})
	check(err)
	return got
}

// endregion

type rec struct{ Token, What string }

// arrivals: 중계기에서 이 작업의 끝 알림을 설정마다 하나씩 기다린다.
func arrivals(id a2a.TaskID) []rec {
	resp, err := http.Get(fmt.Sprintf("%swait?task=%s&n=2", relay, id))
	check(err)
	defer resp.Body.Close()
	var recs []rec
	check(json.NewDecoder(resp.Body).Decode(&recs))
	return recs
}

func check(err error) {
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

func main() {
	ctx := context.Background()
	card, err := agentcard.NewResolver(http.DefaultClient).
		Resolve(ctx, agent)
	check(err)
	c, err := a2aclient.NewFromCard(ctx, card)
	check(err)
	task := send(ctx, c)
	state := strings.TrimPrefix(
		string(task.Status.State), "TASK_STATE_")
	fmt.Println("SendMessage →", state, task.ID)
	got := create(ctx, c, task.ID)
	fmt.Printf("Create → id=%s taskId=%s\n", got.ID, got.TaskID)
	fmt.Printf("  url=%s token=%s\n", got.URL, got.Token)
	// 두 설정으로 가는 알림은 서로 차례가 섞일 수 있어 토큰별로 모은다
	recs := arrivals(task.ID)
	sort.SliceStable(recs, func(i, j int) bool {
		return recs[i].Token < recs[j].Token
	})
	for _, r := range recs {
		fmt.Printf("  %-10s %s\n", r.Token, r.What)
	}
}

//@ norun
