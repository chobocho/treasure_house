// 모르는 필드가 든 답을 Go SDK 클라이언트는 어떻게 읽나.
//
//	go run ./09/strict URL
//
// 상대는 8부의 실험 서버(08/extra_server.ts) — 일곱 실험을 한다.
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

var names = []string{"plain", "task", "status", "result", "envelope",
	"enum", "error"}

func seen(ev a2a.Event) string {
	if t, ok := ev.(*a2a.Task); ok {
		return "받음 " + string(t.Status.State)
	}
	return fmt.Sprintf("받음 %T", ev)
}

func caught(err error) string {
	nf := errors.Is(err, a2a.ErrTaskNotFound)
	return fmt.Sprintf("%T ErrTaskNotFound=%v %q", err, nf, err)
}

// region: probe
func probe(ctx context.Context, c *a2aclient.Client, stream bool) {
	if stream {
		fmt.Println("스트림")
	} else {
		fmt.Println("막는 호출")
	}
	for _, name := range names {
		m := a2a.NewMessage(a2a.MessageRoleUser, a2a.NewTextPart(name))
		m.ID = "s-" + name
		req := &a2a.SendMessageRequest{Message: m}
		if !stream {
			res, err := c.SendMessage(ctx, req)
			if err != nil {
				fmt.Printf("  %-9s %s\n", name, caught(err))
			} else {
				fmt.Printf("  %-9s %s\n", name, seen(res))
			}
			continue
		}
		for ev, err := range c.SendStreamingMessage(ctx, req) {
			if err != nil {
				fmt.Printf("  %-9s %s\n", name, caught(err))
				break
			}
			fmt.Printf("  %-9s %s\n", name, seen(ev))
		}
	}
}

// endregion

func main() {
	ctx := context.Background()
	card, err := agentcard.DefaultResolver.Resolve(ctx, os.Args[1])
	if err != nil {
		panic(err)
	}
	fmt.Printf("카드: %s (모르는 필드는 구조체에 자리가 없다)\n",
		card.Name)
	c, err := a2aclient.NewFromCard(ctx, card)
	if err != nil {
		panic(err)
	}
	defer c.Destroy()
	probe(ctx, c, false)
	probe(ctx, c, true)
}

//@ norun
