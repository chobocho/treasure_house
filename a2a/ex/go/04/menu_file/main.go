// 식사 에이전트에 막는 호출로 식단을 묻고, 아티팩트의 파일 파트를
// 꺼낸다. acceptedOutputModes 에는 "text/markdown 만 받겠다" 고 적는다.
//
//	go run ./04/menu_file 카드주소
package main

import (
	"context"
	"fmt"
	"net/http"
	"os"
	"strings"

	"github.com/a2aproject/a2a-go/v2/a2a"
	"github.com/a2aproject/a2a-go/v2/a2aclient"
	"github.com/a2aproject/a2a-go/v2/a2aclient/agentcard"
)

// region: file
func show(task *a2a.Task) {
	for _, a := range task.Artifacts {
		var kinds []string
		for _, p := range a.Parts {
			kinds = append(kinds, kind(p))
		}
		fmt.Printf("%s: %s\n", a.Name, strings.Join(kinds, " "))
		for _, p := range a.Parts {
			raw, ok := p.Content.(a2a.Raw)
			if !ok {
				continue
			}
			// a2a.Raw 는 []byte — base64 는 SDK 가 이미 풀었다
			fmt.Printf("  %s %s %d바이트\n",
				p.Filename, p.MediaType, len(raw))
			fmt.Print(string(raw))
		}
	}
}

// endregion

func kind(p *a2a.Part) string {
	switch p.Content.(type) {
	case a2a.Text:
		return "text"
	case a2a.Raw:
		return "raw"
	case a2a.URL:
		return "url"
	}
	return "data"
}

func main() {
	ctx := context.Background()
	card, err := agentcard.NewResolver(http.DefaultClient).
		Resolve(ctx, os.Args[1])
	if err != nil {
		panic(err)
	}
	c, err := a2aclient.NewFromCard(ctx, card)
	if err != nil {
		panic(err)
	}
	meals := map[string]any{"nights": 1, "headcount": 30, "vegetarians": 2}
	msg := a2a.NewMessage(a2a.MessageRoleUser, a2a.NewDataPart(meals))
	msg.ID = "menu-go"
	req := &a2a.SendMessageRequest{Message: msg}
	// region: modes
	req.Config = &a2a.SendMessageConfig{
		AcceptedOutputModes: []string{"text/markdown"},
	}
	// endregion
	res, err := c.SendMessage(ctx, req)
	if err != nil {
		panic(err)
	}
	if task, ok := res.(*a2a.Task); ok {
		show(task)
	}
}

//@ norun
