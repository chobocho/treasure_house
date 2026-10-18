// 정산 에이전트의 공개 카드와 확장 카드를 SDK 클라이언트로 견준다 —
// intern 토큰으로 GetExtendedAgentCard 를 부르고, 클라이언트가 들고
// 있는 카드가 바뀌는지 본다.
//
//	go run ./12/xcard 에이전트주소
package main

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"net/url"
	"os"
	"strings"

	"github.com/a2aproject/a2a-go/v2/a2a"
	"github.com/a2aproject/a2a-go/v2/a2aclient"
	"github.com/a2aproject/a2a-go/v2/a2aclient/agentcard"
)

func show(label string, card *a2a.AgentCard) {
	var ids []string
	for _, s := range card.Skills {
		ids = append(ids, s.ID)
	}
	fmt.Printf("%s: 스킬 [%s] · 서명 %d개\n", label,
		strings.Join(ids, ", "), len(card.Signatures))
}

func token(card *a2a.AgentCard, id, secret string) string {
	oauth := card.SecuritySchemes["oauth"].(a2a.OAuth2SecurityScheme)
	flow := oauth.Flows.(a2a.ClientCredentialsOAuthFlow)
	resp, err := http.PostForm(flow.TokenURL, url.Values{
		"grant_type": {"client_credentials"}, "client_id": {id},
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

// region: main
func main() {
	ctx := context.Background()
	card, err := agentcard.DefaultResolver.Resolve(ctx, os.Args[1])
	check(err)
	show("① 공개 카드", card)
	store := a2aclient.NewInMemoryCredentialsStore()
	store.Set("s1", "oauth", a2aclient.AuthCredential(
		token(card, "intern", "intern-secret")))
	client, err := a2aclient.NewFromCard(ctx, card,
		a2aclient.WithCallInterceptors(
			&a2aclient.AuthInterceptor{Service: store}))
	check(err)
	extended, err := client.GetExtendedAgentCard(
		a2aclient.AttachSessionID(ctx, "s1"),
		&a2a.GetExtendedAgentCardRequest{})
	check(err)
	show("② 확장 카드", extended)
	show("③ 클라이언트의 카드", client.Card())
}

// endregion

func check(err error) {
	if err != nil {
		fmt.Println("오류:", err)
		os.Exit(1)
	}
}

//@ norun
