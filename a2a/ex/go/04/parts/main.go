// 파트 네 가지(text·raw·url·data)를 한 메시지에 담아 보낸다.
//
//	go run ./04/parts 카드주소
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

var menu = []byte("# 식단\n- 숯불 바비큐\n") // UTF-8 바이트

// region: parts
func fourParts() []*a2a.Part {
	// 생성 함수가 Content 에 종류별 타입(Text·Raw·URL·Data)을 넣는다
	raw := a2a.NewRawPart(menu)
	// NewRawPart 는 파일 이름·미디어 타입을 받지 않는다 — 필드로
	raw.Filename, raw.MediaType = "menu.md", "text/markdown"
	url := a2a.NewFileURLPart(
		"https://treasure-house.example/map.png", "image/png")
	url.Filename = "map.png"
	return []*a2a.Part{
		a2a.NewTextPart("워크숍 자료 넷을 보냅니다"),
		raw,
		url,
		a2a.NewDataPart([]any{"숙소", "식사", "교통"}),
	}
}

// endregion

func main() {
	ctx := context.Background()
	r := agentcard.NewResolver(http.DefaultClient)
	card, err := r.Resolve(ctx, os.Args[1])
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	c, err := a2aclient.NewFromCard(ctx, card)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	msg := a2a.NewMessage(a2a.MessageRoleUser, fourParts()...)
	msg.ID = "parts-go"
	req := &a2a.SendMessageRequest{Message: msg}
	res, err := c.SendMessage(ctx, req)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	fmt.Printf("답: %T\n", res)
	if m, ok := res.(*a2a.Message); ok {
		for _, p := range m.Parts {
			fmt.Println(p.Text())
		}
	}
}

//@ norun
