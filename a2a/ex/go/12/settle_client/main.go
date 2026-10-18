// 정산 에이전트를 SDK 클라이언트로 부른다 — 토큰 없이 한 번, 카드의
// tokenUrl 에서 토큰을 받아 AuthInterceptor 로 한 번.
//
//	go run ./12/settle_client 에이전트주소 client_id client_secret
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

var small = map[string]any{
	"items":  []any{map[string]any{"name": "숙소", "amount": 2100000}},
	"budget": 6000000,
}

func request(id string) *a2a.SendMessageRequest {
	msg := a2a.NewMessage(a2a.MessageRoleUser, a2a.NewDataPart(small))
	msg.ID = id
	return &a2a.SendMessageRequest{Message: msg}
}

// region: token
// getToken: 카드가 알려 준 tokenUrl 에 client_credentials 로 묻는다.
func getToken(card *a2a.AgentCard, id, secret string) string {
	oauth := card.SecuritySchemes["oauth"].(a2a.OAuth2SecurityScheme)
	flow := oauth.Flows.(a2a.ClientCredentialsOAuthFlow)
	resp, err := http.PostForm(flow.TokenURL, url.Values{
		"grant_type":    {"client_credentials"},
		"client_id":     {id},
		"client_secret": {secret},
	})
	check(err)
	defer resp.Body.Close()
	var got struct {
		AccessToken string `json:"access_token"`
	}
	check(json.NewDecoder(resp.Body).Decode(&got))
	return got.AccessToken
}

// endregion

// region: main
func main() {
	ctx := context.Background()
	card, err := agentcard.DefaultResolver.Resolve(ctx, os.Args[1])
	check(err)
	store := a2aclient.NewInMemoryCredentialsStore() // 처음엔 비었다
	auth := &a2aclient.AuthInterceptor{Service: store}
	client, err := a2aclient.NewFromCard(ctx, card,
		a2aclient.WithCallInterceptors(auth))
	check(err)
	if _, err := client.SendMessage(ctx, request("go-1")); err != nil {
		fmt.Println("① 토큰 없이 →", err)
	}
	token := getToken(card, os.Args[2], os.Args[3])
	fmt.Println("② 받은 토큰", token)
	store.Set("s1", "oauth", a2aclient.AuthCredential(token))
	res, err := client.SendMessage(
		a2aclient.AttachSessionID(ctx, "s1"), request("go-2"))
	check(err)
	task := res.(*a2a.Task)
	sheet := task.Artifacts[0].Parts[0].Data().(map[string]any)
	fmt.Printf("③ 토큰 달고 → %s, approvedBy %v\n",
		task.Status.State, sheet["approvedBy"])
}

// endregion

func check(err error) {
	if err != nil {
		fmt.Println(err)
		os.Exit(1)
	}
}

//@ norun
