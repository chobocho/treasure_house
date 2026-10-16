// contextId·taskId 규칙(§3.4)을 접수 에이전트에 차례로 두드려 본다.
// 여섯 번 보내고, 답의 상태·작업 id·맥락 id 나 오류를 한 줄씩 찍는다.
//
//	go run ./04/ctx_rules 카드주소
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

var n int // messageId 가 겹치지 않게

// region: send
func send(c *a2aclient.Client, label, text string,
	taskID a2a.TaskID, contextID string) *a2a.Task {
	n++
	msg := a2a.NewMessage(a2a.MessageRoleUser, a2a.NewTextPart(text))
	msg.ID = fmt.Sprintf("ctx-go-%d", n)
	msg.TaskID, msg.ContextID = taskID, contextID // "" 이면 빠진다
	req := &a2a.SendMessageRequest{Message: msg}
	res, err := c.SendMessage(context.Background(), req)
	if err != nil {
		fmt.Printf("%s %v\n", label, err)
		return nil
	}
	t := res.(*a2a.Task)
	st := strings.TrimPrefix(string(t.Status.State), "TASK_STATE_")
	fmt.Printf("%s %s task=%s ctx=%s\n", label, st, t.ID, t.ContextID)
	return t
}

// endregion

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
	// region: rules
	t1 := send(c, "①", "워크숍 접수", "", "")
	send(c, "②", "20명", "", t1.ContextID)
	send(c, "③", "30명", t1.ID, "ctx-다른-맥락")
	send(c, "④", "30명", t1.ID, "")
	send(c, "⑤", "30명", "t-없는-작업", "")
	send(c, "⑥", "25명", "", "ctx-워크숍")
	// endregion
}

//@ norun
