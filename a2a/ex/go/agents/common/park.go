package common

import (
	"context"
	"errors"
	"iter"
	"sync"

	"github.com/a2aproject/a2a-go/v2/a2a"
	"github.com/a2aproject/a2a-go/v2/a2asrv"
)

// region: park
// Go SDK 는 AUTH_REQUIRED 를 '실행이 살아서 기다리는 상태'로 본다.
// INPUT_REQUIRED 와 달리 실행을 끝내지 않고, 그 작업에 새 메시지가
// 오면 'execution is already in progress' 로 거절한다. 그런데 파이썬
// ·TS 쪽은 결재 토큰을 같은 taskId 의 새 메시지로 보낸다. 그래서
// 기다리는 실행기를 여기 맡겨 두고(park), 새 메시지를 넘겨준다.

// Reply 는 기다리던 실행기에 넘기는 이어 말하기 한 번이다.
type Reply struct {
	Task *a2a.Task    // 넘기는 순간 저장소에 있던 작업
	Msg  *a2a.Message // 이번 메시지
	User *a2asrv.User // 이번 요청의 사용자(새 토큰의 스코프)
}

var parked sync.Map // a2a.TaskID → chan Reply

// AwaitReply 는 상태를 AUTH_REQUIRED 로 알리고 다음 메시지를
// 기다린다. 받으면 그 메시지를 history 에 넣은 Task 를 WORKING 으로
// 다시 싣는다(Begin 과 같은 까닭). 취소되면 false.
func (u *Updater) AwaitReply(
	ctx context.Context, parts ...*a2a.Part,
) (Reply, bool) {
	id := u.ec.TaskID
	// 알리기 전에 자리를 만든다 — 알린 뒤에 만들면 그 틈에 온 답을
	// 놓칠 수 있다.
	ch := make(chan Reply, 1)
	parked.Store(id, ch)
	defer parked.CompareAndDelete(id, ch)
	if !u.Status(a2a.TaskStateAuthRequired, parts...) {
		return Reply{}, false
	}
	select {
	case r := <-ch:
		t := working(r.Task)
		t.History = append(t.History[:len(t.History):len(t.History)],
			r.Msg)
		return r, u.yield(t, nil)
	case <-ctx.Done():
		return Reply{}, false
	}
}

// endregion

// waiter 는 요청 처리기를 감싸, 기다리는 작업으로 온 메시지를
// 그 실행기에 넘기고, AUTH_REQUIRED 에서 스트림을 닫는다(SDK 는
// 실행이 끝날 때까지 스트림을 열어 둔다).
type waiter struct{ a2asrv.RequestHandler }

func (h waiter) SendMessage(
	ctx context.Context, req *a2a.SendMessageRequest,
) (a2a.SendMessageResult, error) {
	ch, ok := take(req)
	if !ok {
		return h.RequestHandler.SendMessage(ctx, req)
	}
	for _, err := range h.resume(ctx, req, ch) {
		if err != nil {
			return nil, err
		}
	}
	id := req.Message.TaskID
	return h.GetTask(ctx, &a2a.GetTaskRequest{ID: id})
}

func (h waiter) SendStreamingMessage(
	ctx context.Context, req *a2a.SendMessageRequest,
) iter.Seq2[a2a.Event, error] {
	events := h.RequestHandler.SendStreamingMessage(ctx, req)
	if ch, ok := take(req); ok {
		events = h.resume(ctx, req, ch)
	}
	return func(yield func(a2a.Event, error) bool) {
		for ev, err := range events {
			if !yield(ev, err) || paused(ev) {
				return
			}
		}
	}
}

// resume 은 실행기에 메시지를 넘기고 그 뒤의 사건을 흘린다.
func (h waiter) resume(
	ctx context.Context, req *a2a.SendMessageRequest, ch chan Reply,
) iter.Seq2[a2a.Event, error] {
	return func(yield func(a2a.Event, error) bool) {
		id := req.Message.TaskID
		sub := h.SubscribeToTask(ctx,
			&a2a.SubscribeToTaskRequest{ID: id})
		next, stop := iter.Pull2(sub)
		defer stop()
		// 구독의 첫 사건은 저장소의 작업 그대로(멈춘 상태)다. 내보내지
		// 않고 실행기가 이어 갈 바탕으로 넘긴다.
		first, err, _ := next()
		task, isTask := first.(*a2a.Task)
		if err != nil || !isTask {
			yield(nil, errors.Join(err, a2a.ErrTaskNotFound))
			return
		}
		user := &a2asrv.User{}
		if cc, ok := a2asrv.CallContextFrom(ctx); ok {
			user = cc.User
		}
		ch <- Reply{Task: task, Msg: req.Message, User: user}
		for {
			ev, err, ok := next()
			if !ok || !yield(ev, err) || paused(ev) {
				return
			}
		}
	}
}

// take 는 메시지가 기다리는 작업으로 온 것이면 그 자리를 꺼낸다.
// 꺼내면서 지우므로 같은 답이 두 번 넘어가지 않는다.
func take(req *a2a.SendMessageRequest) (chan Reply, bool) {
	if req == nil || req.Message == nil || req.Message.TaskID == "" {
		return nil, false
	}
	v, ok := parked.LoadAndDelete(req.Message.TaskID)
	if !ok {
		return nil, false
	}
	return v.(chan Reply), true
}

func paused(ev a2a.Event) bool {
	switch v := ev.(type) {
	case *a2a.TaskStatusUpdateEvent:
		return v.Status.State == a2a.TaskStateAuthRequired
	case *a2a.Task:
		return v.Status.State == a2a.TaskStateAuthRequired
	}
	return false
}
