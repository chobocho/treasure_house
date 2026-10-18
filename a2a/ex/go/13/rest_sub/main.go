// SDK 클라이언트의 SubscribeToTask 는 HTTP+JSON 에서 어떤 동사로 가나.
// 없는 작업에 잇기만 한 번 — 동사는 탭이 본다(5장).
//
//	go run ./13/rest_sub URL
package main

import (
	"context"
	"fmt"
	"os"

	"github.com/a2aproject/a2a-go/v2/a2a"
	"github.com/a2aproject/a2a-go/v2/a2aclient"
	"github.com/a2aproject/a2a-go/v2/a2aclient/agentcard"
)

// region: sub
func main() {
	ctx := context.Background()
	card, err := agentcard.DefaultResolver.Resolve(ctx, os.Args[1])
	if err != nil {
		panic(err)
	}
	client, err := a2aclient.NewFromCard(ctx, card)
	if err != nil {
		panic(err)
	}
	req := &a2a.SubscribeToTaskRequest{ID: "t-nope"}
	for _, err := range client.SubscribeToTask(ctx, req) {
		if err != nil {
			fmt.Println("잇기:", err)
		}
	}
}

// endregion
//@ norun
