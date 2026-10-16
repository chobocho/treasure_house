// 카드에 없는 기능 셋을 SDK 클라이언트로 불러 본다. 클라이언트가
// 카드를 먼저 보고 막는지, 서버까지 가서 오류를 받는지 보려는 것.
//
//	go run ./03/caps_probe 카드주소
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

// region: probe
func probe(ctx context.Context, c *a2aclient.Client) {
	msg := a2a.NewMessage(a2a.MessageRoleUser,
		a2a.NewTextPart("안녕하세요"))
	msg.ID = "probe-1"
	req := &a2a.SendMessageRequest{Message: msg}
	// SendStreamingMessage 는 카드가 허락하면 스트림, 아니면 막는 호출
	for ev, err := range c.SendStreamingMessage(ctx, req) {
		if err != nil {
			fmt.Println("① 메시지 →", err)
			continue
		}
		fmt.Printf("① 메시지 → %T\n", ev)
	}
	hook := &a2a.PushConfig{
		TaskID: "t-1", URL: "http://127.0.0.1:10399/hook",
	}
	if _, err := c.CreateTaskPushConfig(ctx, hook); err != nil {
		fmt.Println("② 푸시 설정 →", err)
	}
	xreq := &a2a.GetExtendedAgentCardRequest{}
	if card, err := c.GetExtendedAgentCard(ctx, xreq); err != nil {
		fmt.Println("③ 확장 카드 →", err)
	} else {
		fmt.Println("③ 확장 카드 →", card.Name)
	}
}

// endregion

func main() {
	ctx := context.Background()
	r := agentcard.NewResolver(http.DefaultClient)
	card, err := r.Resolve(ctx, os.Args[1])
	if err == nil {
		var c *a2aclient.Client
		if c, err = a2aclient.NewFromCard(ctx, card); err == nil {
			probe(ctx, c)
			return
		}
	}
	fmt.Fprintln(os.Stderr, err)
	os.Exit(1)
}

//@ norun
