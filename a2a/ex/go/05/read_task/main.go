// 끝난 숙소 Task 를 받아 필드를 하나씩 읽는다(Go SDK 의 모양으로).
//
//	go run ./05/read_task 카드주소
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

var request = map[string]any{
	"date": "2026-10-30", "nights": 1, "headcount": 30,
}

// region: read
// has 는 포인터·맵이 nil 인지로 있음/없음을 가린다
func has(nilable bool) string {
	if nilable {
		return "없음"
	}
	return "있음"
}

func read(t *a2a.Task) {
	fmt.Println("id        :", t.ID)
	fmt.Println("contextId :", t.ContextID)
	st := t.Status // 구조체 값이다(포인터가 아니다)
	fmt.Println("state     :", st.State)
	fmt.Printf("timestamp : %T %s\n",
		st.Timestamp, has(st.Timestamp == nil))
	fmt.Println("message   :", has(st.Message == nil))
	for _, a := range t.Artifacts {
		var kinds []string
		for _, p := range a.Parts {
			kinds = append(kinds, fmt.Sprintf("%T", p.Content))
		}
		fmt.Println("artifact  :", a.Name, kinds)
	}
	for _, m := range t.History {
		fmt.Println("history   :", m.Role, m.ID)
	}
	fmt.Println("metadata  :", has(t.Metadata == nil))
}

// endregion

func check(err error) {
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

func main() {
	ctx := context.Background()
	r := agentcard.NewResolver(http.DefaultClient)
	card, err := r.Resolve(ctx, os.Args[1])
	check(err)
	c, err := a2aclient.NewFromCard(ctx, card)
	check(err)
	msg := a2a.NewMessage(a2a.MessageRoleUser, a2a.NewDataPart(request))
	msg.ID = "read-go"
	req := &a2a.SendMessageRequest{Message: msg}
	res, err := c.SendMessage(ctx, req)
	check(err)
	read(res.(*a2a.Task)) // 숙소 에이전트는 Task 로 답한다
}

//@ norun
