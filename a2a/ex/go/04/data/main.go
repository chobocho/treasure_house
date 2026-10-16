// 숙소 요청 {date, nights, headcount} 를 DataPart 로 보낸다.
// 답이 Message 면 글을, Task 면 상태와 견적의 수 셋을 찍는다.
//
//	go run ./04/data 카드주소
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

// region: send
type lodgingRequest struct {
	Date      string `json:"date"`
	Nights    int    `json:"nights"`
	Headcount int    `json:"headcount"`
}

func lodgingMessage() *a2a.Message {
	req := lodgingRequest{Date: "2026-10-30", Nights: 1, Headcount: 30}
	// Data 는 any — 구조체를 넣으면 encoding/json 이 그대로 적는다
	msg := a2a.NewMessage(a2a.MessageRoleUser, a2a.NewDataPart(req))
	msg.ID = "data-go"
	return msg
}

// endregion

// region: read
func showQuote(task *a2a.Task) {
	fmt.Println("task", task.Status.State)
	quote, _ := task.Artifacts[0].Parts[0].Data().(map[string]any)
	for _, k := range []string{"headcount", "rooms", "total"} {
		fmt.Printf("  %s: %T %#v\n", k, quote[k], quote[k])
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
	req := &a2a.SendMessageRequest{Message: lodgingMessage()}
	res, err := c.SendMessage(ctx, req)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	// region: dispatch
	// 결과는 a2a.SendMessageResult 인터페이스 — 타입으로 가른다
	switch v := res.(type) {
	case *a2a.Task:
		showQuote(v)
	case *a2a.Message:
		for _, p := range v.Parts {
			fmt.Println(p.Text())
		}
	}
	// endregion
}

//@ norun
