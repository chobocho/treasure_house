// 스트리밍을 켜지 않은 카드(3부의 안내 에이전트)에 SDK 클라이언트로
// 스트림 보내기와 SubscribeToTask 를 부른다 — 무엇이 서버까지 가나.
//
//	go run ./10/nosub URL
package main

import (
	"context"
	"errors"
	"fmt"
	"os"

	"github.com/a2aproject/a2a-go/v2/a2a"
	"github.com/a2aproject/a2a-go/v2/a2aclient"
	"github.com/a2aproject/a2a-go/v2/a2aclient/agentcard"
)

// region: probe
func run(ctx context.Context, url string) error {
	card, err := agentcard.DefaultResolver.Resolve(ctx, url)
	if err != nil {
		return err
	}
	c, err := a2aclient.NewFromCard(ctx, card)
	if err != nil {
		return err
	}
	defer c.Destroy()
	hi := a2a.NewTextPart("안녕하세요")
	m := a2a.NewMessage(a2a.MessageRoleUser, hi)
	m.ID = "n-1"
	req := &a2a.SendMessageRequest{Message: m}
	for ev, err := range c.SendStreamingMessage(ctx, req) {
		if err != nil {
			return err
		}
		fmt.Printf("① 스트림 보내기 → %T\n", ev)
	}
	sub := &a2a.SubscribeToTaskRequest{ID: "t-1"}
	for ev, err := range c.SubscribeToTask(ctx, sub) {
		if err != nil {
			fmt.Println("② 구독 →", err)
			fmt.Println("   errors.Is ErrUnsupportedOperation:",
				errors.Is(err, a2a.ErrUnsupportedOperation))
			break
		}
		fmt.Printf("② 구독 → %T\n", ev)
	}
	return nil
}

// endregion

func main() {
	if err := run(context.Background(), os.Args[1]); err != nil {
		fmt.Fprintln(os.Stderr, "오류:", err)
		os.Exit(1)
	}
}

//@ norun
