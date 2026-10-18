// 큰 정산을 조회 토큰으로 맡겨 AUTH_REQUIRED 를 받고, 결재 스코프가
// 든 새 토큰으로 같은 작업에 이어 말해 끝낸다. SDK 클라이언트 하나,
// 자격 증명 저장소의 토큰만 바꾼다.
//
//	go run ./12/approve 에이전트주소
package main

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"net/url"
	"os"

	"github.com/a2aproject/a2a-go/v2/a2a"
	"github.com/a2aproject/a2a-go/v2/a2aclient"
	"github.com/a2aproject/a2a-go/v2/a2aclient/agentcard"
)

var big = map[string]any{
	"items": []any{
		map[string]any{"name": "숙소", "amount": 2100000},
		map[string]any{"name": "식사", "amount": 1542000},
		map[string]any{"name": "교통", "amount": 1200000},
	},
	"budget": 6000000,
}

func token(card *a2a.AgentCard, scope string) string {
	oauth := card.SecuritySchemes["oauth"].(a2a.OAuth2SecurityScheme)
	flow := oauth.Flows.(a2a.ClientCredentialsOAuthFlow)
	resp, err := http.PostForm(flow.TokenURL, url.Values{
		"grant_type": {"client_credentials"}, "client_id": {"planner"},
		"client_secret": {"planner-secret"}, "scope": {scope},
	})
	check(err)
	defer resp.Body.Close()
	var got struct {
		AccessToken string `json:"access_token"`
	}
	check(json.NewDecoder(resp.Body).Decode(&got))
	return got.AccessToken
}

// region: main
func main() {
	ctx := context.Background()
	card, err := agentcard.DefaultResolver.Resolve(ctx, os.Args[1])
	check(err)
	store := a2aclient.NewInMemoryCredentialsStore()
	client, err := a2aclient.NewFromCard(ctx, card,
		a2aclient.WithCallInterceptors(
			&a2aclient.AuthInterceptor{Service: store}))
	check(err)
	ctx = a2aclient.AttachSessionID(ctx, "s1")
	send := func(m *a2a.Message) *a2a.Task {
		res, err := client.SendMessage(ctx,
			&a2a.SendMessageRequest{Message: m})
		check(err)
		return res.(*a2a.Task)
	}
	read := token(card, "payment:read")
	store.Set("s1", "oauth", a2aclient.AuthCredential(read))
	m := a2a.NewMessage(a2a.MessageRoleUser, a2a.NewDataPart(big))
	m.ID = "a-1"
	task := send(m)
	fmt.Printf("① %s → %s\n", read, task.Status.State)
	fmt.Printf("   %s\n", task.Status.Message.Parts[0].Text())
	both := token(card, "payment:read payment:approve")
	store.Set("s1", "oauth", a2aclient.AuthCredential(both)) // 토큰만
	m = a2a.NewMessageForTask(a2a.MessageRoleUser, task,
		a2a.NewTextPart("결재합니다"))
	m.ID = "a-2"
	task = send(m)
	sheet := task.Artifacts[0].Parts[0].Data().(map[string]any)
	fmt.Printf("② %s → %s, approvedBy %v\n", both,
		task.Status.State, sheet["approvedBy"])
}

// endregion

func check(err error) {
	if err != nil {
		fmt.Println("오류:", err)
		os.Exit(1)
	}
}

//@ norun
