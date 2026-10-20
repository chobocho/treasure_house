// 카드가 판 0.3 문 하나만 적은 에이전트에 Go SDK 클라이언트로 묻는다.
// 옛 판의 전송은 a2acompat/a2av0 에 있고, 팩토리에 끼워야 쓴다.
//
//	go run ./14/old_client URL
package main

import (
	"context"
	"fmt"
	"os"

	"github.com/a2aproject/a2a-go/v2/a2a"
	"github.com/a2aproject/a2a-go/v2/a2aclient"
	"github.com/a2aproject/a2a-go/v2/a2aclient/agentcard"
	"github.com/a2aproject/a2a-go/v2/a2acompat/a2av0"
)

// region: send
func run(ctx context.Context, url string) error {
	card, err := agentcard.DefaultResolver.Resolve(ctx, url)
	if err != nil {
		return err
	}
	old := a2av0.WithJSONRPCTransport(a2av0.JSONRPCTransportConfig{})
	client, err := a2aclient.NewFromCard(ctx, card, old)
	if err != nil {
		return err
	}
	defer client.Destroy()
	m := a2a.NewMessage(a2a.MessageRoleUser, a2a.NewDataPart(
		map[string]any{"date": "2026-10-30", "nights": 1,
			"headcount": 30}))
	m.ID = "o-1"
	req := &a2a.SendMessageRequest{Message: m}
	res, err := client.SendMessage(ctx, req)
	if err != nil {
		return err
	}
	if t, ok := res.(*a2a.Task); ok {
		data, _ := t.Artifacts[0].Parts[0].Data().(map[string]any)
		fmt.Println(t.Status.State, data["venueName"])
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
