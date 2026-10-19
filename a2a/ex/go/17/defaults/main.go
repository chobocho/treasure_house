// SDK 기본값 그대로 — 6초 걸리는 배차를 막는 호출로 맡긴다.
//
//	go run ./17/defaults 카드주소
package main

import (
	"context"
	"fmt"
	"net/http"
	"os"

	"github.com/a2aproject/a2a-go/v2/a2a"
	"github.com/a2aproject/a2a-go/v2/a2aclient"
	"github.com/a2aproject/a2a-go/v2/a2aclient/agentcard"
)

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
	// region: make
	// 전송을 고르지 않으면 SDK 가 http.Client{Timeout: 3분} 을 짓는다
	c, err := a2aclient.NewFromCard(ctx, card)
	// endregion
	check(err)
	bus := map[string]any{
		"headcount": 30, "nights": 1, "depart": "강남역"}
	msg := a2a.NewMessage(a2a.MessageRoleUser, a2a.NewDataPart(bus))
	msg.ID = "m-default"
	req := &a2a.SendMessageRequest{Message: msg}
	res, err := c.SendMessage(ctx, req)
	check(err)
	fmt.Println("SendMessage →", res.(*a2a.Task).Status.State)
}

// endregion

//@ norun
