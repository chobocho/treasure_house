// referenceTaskIds 를 SDK 가 작업으로 풀어 주나 — 처리기를 HTTP 없이
// 직접 부른다. 다른 서버의 작업 하나와 이 서버의 작업 하나를 가리킨다.
//
//	go run ./15/refs
package main

import (
	"context"
	"fmt"
	"iter"
	"strings"

	"github.com/a2aproject/a2a-go/v2/a2a"
	"github.com/a2aproject/a2a-go/v2/a2asrv"
	"github.com/a2aproject/a2a-go/v2/a2asrv/taskstore"

	"example.com/workshop/agents/common"
)

// region: seen
// seen 은 실행기가 받은 RelatedTasks 의 id 를 끝 상태 메시지로 알린다.
type seen struct{}

func (seen) Execute(ctx context.Context, ec *a2asrv.ExecutorContext,
) iter.Seq2[a2a.Event, error] {
	return func(yield func(a2a.Event, error) bool) {
		_, up, ok := common.Begin(ec, yield)
		if !ok {
			return
		}
		var ids []string
		for _, t := range ec.RelatedTasks {
			ids = append(ids, string(t.ID))
		}
		n := len(ids)
		if n == 0 {
			ids = []string{"없음"}
		}
		text := fmt.Sprintf("RelatedTasks %d개: %s", n,
			strings.Join(ids, ", "))
		up.Status(a2a.TaskStateCompleted, common.TextPart(text))
	}
}

func (seen) Cancel(context.Context, *a2asrv.ExecutorContext,
) iter.Seq2[a2a.Event, error] {
	return func(func(a2a.Event, error) bool) {}
}

func handler(fill bool) a2asrv.RequestHandler {
	store := taskstore.NewInMemory(nil)
	opts := []a2asrv.RequestHandlerOption{a2asrv.WithTaskStore(store)}
	if fill { // 가로채기를 달아야 채운다
		loader := &a2asrv.ReferencedTasksLoader{Store: store}
		hook := a2asrv.WithExecutorContextInterceptor(loader)
		opts = append(opts, hook)
	}
	return a2asrv.NewHandler(seen{}, opts...)
}

// endregion

func send(h a2asrv.RequestHandler, text string,
	refs ...a2a.TaskID) *a2a.Task {
	m := a2a.NewMessage(a2a.MessageRoleUser, common.TextPart(text))
	m.ReferenceTasks = refs
	res, err := h.SendMessage(context.Background(),
		&a2a.SendMessageRequest{Message: m})
	if err != nil {
		panic(err)
	}
	return res.(*a2a.Task)
}

// region: main
func main() {
	other := send(handler(false), "숙소 견적") // 다른 서버
	fmt.Println("다른 서버의 작업", other.ID)
	for _, fill := range []bool{false, true} {
		h := handler(fill)
		mine := send(h, "앞 작업")
		fmt.Println("이 서버의 작업", mine.ID)
		t := send(h, "정산", other.ID, mine.ID)
		word := map[bool]string{false: "끔(기본)", true: "켬"}[fill]
		fmt.Printf("  채우기 %s → %s\n", word,
			common.TextOf(t.Status.Message))
	}
}

// endregion
