// 이어 말하기 — 두 번째 Execute 의 StoredTask 에는 무엇이 들어 있나.
//
//	go run ./09/follow
package main

import (
	"context"
	"fmt"
	"iter"
	"strings"

	"github.com/a2aproject/a2a-go/v2/a2a"
	"github.com/a2aproject/a2a-go/v2/a2asrv"
)

func who(t *a2a.Task) string {
	var s []string
	for _, m := range t.History {
		s = append(s, string(m.Role)+" "+m.ID)
	}
	return strings.Join(s, " · ")
}

// region: executor
func askOnce(
	ctx context.Context, ec *a2asrv.ExecutorContext,
) iter.Seq2[a2a.Event, error] {
	return func(yield func(a2a.Event, error) bool) {
		if ec.StoredTask == nil { // 1차: Task 를 짓고 되묻는다
			fmt.Println("1차: StoredTask 없음")
			if !yield(a2a.NewSubmittedTask(ec, ec.Message), nil) {
				return
			}
			q := a2a.NewMessageForTask(a2a.MessageRoleAgent, ec,
				a2a.NewTextPart("인원은?"))
			q.ID = "q-1"
			yield(a2a.NewStatusUpdateEvent(ec,
				a2a.TaskStateInputRequired, q), nil)
			return
		}
		fmt.Println("2차: StoredTask 있음")
		fmt.Println("   이력:", who(ec.StoredTask))
		last := ec.StoredTask.History[len(ec.StoredTask.History)-1]
		fmt.Println("   이번 메시지가 이미 있나:", last.ID == "m-2")
		// 저장된 Task 가 있으니 상태 갱신부터 내도 된다
		yield(a2a.NewStatusUpdateEvent(ec,
			a2a.TaskStateCompleted, nil), nil)
	}
}

// endregion

func main() {
	h := a2asrv.NewHandler(a2asrv.AgentExecutorFunc(askOnce))
	ctx := context.Background()
	say := func(id string, task a2a.TaskID) *a2a.SendMessageRequest {
		m := a2a.NewMessage(a2a.MessageRoleUser,
			a2a.NewTextPart("30명"))
		m.ID, m.TaskID = id, task
		return &a2a.SendMessageRequest{Message: m}
	}
	res, err := h.SendMessage(ctx, say("m-1", ""))
	if err != nil {
		panic(err)
	}
	t := res.(*a2a.Task)
	fmt.Println("   →", t.Status.State)
	if _, err := h.SendMessage(ctx, say("m-2", t.ID)); err != nil {
		panic(err)
	}
	got, _ := h.GetTask(ctx, &a2a.GetTaskRequest{ID: t.ID})
	fmt.Println("저장된 이력:", who(got))
}
