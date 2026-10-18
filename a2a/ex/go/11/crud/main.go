// 푸시 설정 CRUD — 설정 둘(요청에 실은 hook-1, Create 한 hook-2)을 단
// 작업에 Get·List·Delete 를 차례로 한다. 지운 설정으로는 알림이 더 가지
// 않는지 중계기(relay.py)에서 본다. 마지막은 없는 설정을 Get.
//
//	go run ./11/crud 에이전트 웹훅 중계기
package main

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"net/http"
	"os"
	"sort"

	"github.com/a2aproject/a2a-go/v2/a2a"
	"github.com/a2aproject/a2a-go/v2/a2aclient"
	"github.com/a2aproject/a2a-go/v2/a2aclient/agentcard"
)

var agent, hook, relay = os.Args[1], os.Args[2], os.Args[3]

var bus = map[string]any{
	"headcount": 30, "nights": 1, "depart": "강남역",
}

func setup(ctx context.Context, c *a2aclient.Client) a2a.TaskID {
	msg := a2a.NewMessage(a2a.MessageRoleUser, a2a.NewDataPart(bus))
	msg.ID = "crud-1"
	res, err := c.SendMessage(ctx, &a2a.SendMessageRequest{
		Message: msg,
		Config: &a2a.SendMessageConfig{ReturnImmediately: true,
			PushConfig: &a2a.PushConfig{
				ID: "hook-1", URL: hook, Token: "tok-1"}},
	})
	check(err)
	id := res.(*a2a.Task).ID
	_, err = c.CreateTaskPushConfig(ctx, &a2a.PushConfig{
		TaskID: id, ID: "hook-2", URL: hook, Token: "tok-2"})
	check(err)
	return id
}

// region: list
func show(ctx context.Context, c *a2aclient.Client, id a2a.TaskID) {
	cfgs, err := c.ListTaskPushConfigs(ctx,
		&a2a.ListTaskPushConfigRequest{TaskID: id})
	check(err)
	// Go 서버는 맵을 돌아 돌려준다 — 차례가 그때그때라
	// 토큰으로 줄 세운다
	got := []string{}
	for _, cf := range cfgs {
		got = append(got, cf.ID+":"+cf.Token)
	}
	sort.Strings(got)
	fmt.Printf("List → %d개 %v\n", len(got), got)
}

// endregion

// region: crud
func crud(ctx context.Context, c *a2aclient.Client, id a2a.TaskID) {
	get := &a2a.GetTaskPushConfigRequest{TaskID: id, ID: "hook-2"}
	cf, err := c.GetTaskPushConfig(ctx, get)
	check(err)
	fmt.Printf("Get hook-2 → url=%s token=%s\n", cf.URL, cf.Token)
	show(ctx, c, id)
	gone := &a2a.DeleteTaskPushConfigRequest{TaskID: id, ID: "hook-1"}
	for n := 1; n <= 2; n++ { // 두 번 지운다 — 명세는 멱등(idempotent)
		if err := c.DeleteTaskPushConfig(ctx, gone); err != nil {
			fmt.Printf("Delete hook-1 (%d) → %v\n", n, err)
		} else {
			fmt.Printf("Delete hook-1 (%d) → 오류 없음\n", n)
		}
	}
	show(ctx, c, id)
	get.ID = "hook-1"
	_, err = c.GetTaskPushConfig(ctx, get)
	fmt.Println("Get hook-1 →", err)
	// 와이어의 오류 코드가 클라이언트에서 어느 sentinel 이 되었나
	fmt.Println("  ErrTaskNotFound:",
		errors.Is(err, a2a.ErrTaskNotFound),
		"ErrInternalError:", errors.Is(err, a2a.ErrInternalError))
}

// endregion

// arrivals: tok-2 의 끝 알림을 기다린 뒤, 토큰마다 받은 것을 센다.
func arrivals(id a2a.TaskID) {
	resp, err := http.Get(
		fmt.Sprintf("%swait?task=%s&token=tok-2", relay, id))
	check(err)
	defer resp.Body.Close()
	var recs []struct{ Token, What string }
	check(json.NewDecoder(resp.Body).Decode(&recs))
	seen := map[string][]string{}
	for _, r := range recs {
		seen[r.Token] = append(seen[r.Token], r.What)
	}
	for _, t := range []string{"tok-1", "tok-2"} {
		fmt.Printf("  %s %d건 — 첫 %s\n", t, len(seen[t]), seen[t][0])
	}
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
	id := setup(ctx, c)
	fmt.Println("작업", id)
	crud(ctx, c, id)
	arrivals(id)
}

//@ norun
