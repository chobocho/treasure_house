package common

import (
	"context"
	"iter"
	"time"

	"github.com/a2aproject/a2a-go/v2/a2a"
	"github.com/a2aproject/a2a-go/v2/a2asrv"
)

// Updater 는 파이썬 SDK 의 TaskUpdater 몫이다. Go SDK 의 실행기는
// 이벤트를 yield 로 내보내는 반복자라서, yield 를 품고 이벤트를 만든다.
// 메서드가 false 를 돌려주면 받는 쪽이 끝난 것이니 실행을 멈춘다.
type Updater struct {
	ec    *a2asrv.ExecutorContext
	yield func(a2a.Event, error) bool
}

func NewUpdater(
	ec *a2asrv.ExecutorContext, yield func(a2a.Event, error) bool,
) *Updater {
	return &Updater{ec: ec, yield: yield}
}

// Message 는 이 작업에 묶인 에이전트 쪽(ROLE_AGENT) 메시지다.
func (u *Updater) Message(parts ...*a2a.Part) *a2a.Message {
	role := a2a.MessageRoleAgent
	return a2a.NewMessageForTask(role, u.ec, parts...)
}

func (u *Updater) Status(state a2a.TaskState, parts ...*a2a.Part) bool {
	var msg *a2a.Message
	if len(parts) > 0 {
		msg = u.Message(parts...)
	}
	return u.yield(a2a.NewStatusUpdateEvent(u.ec, state, msg), nil)
}

// Chunk 는 아티팩트 한 조각의 자리: id(빈 값이면 새로), 이어 붙이기,
// 마지막 조각.
type Chunk struct {
	ID     a2a.ArtifactID
	Append bool
	Last   bool
}

func (u *Updater) Artifact(
	name string, c Chunk, parts ...*a2a.Part,
) bool {
	ev := a2a.NewArtifactEvent(u.ec, parts...)
	if c.ID != "" {
		ev.Artifact.ID = c.ID
	}
	ev.Artifact.Name = name
	ev.Append, ev.LastChunk = c.Append, c.Last
	return u.yield(ev, nil)
}

// region: begin
// Begin 은 실행을 시작한다: 첫 메시지면 SUBMITTED Task 를 싣는다.
// 이어 말하기(같은 taskId)에서도 지금의 Task 를 다시 싣는다 — 명세
// 3.1.2 는 Task 스트림이 Task 로 시작하기를 요구하는데, Go SDK 는
// 이어 말하기 스트림을 Task 없이 시작한다(첫 이벤트 강제도 없다).
// 답을 받았으니 상태는 WORKING 으로 — 멈춘 상태 그대로 실으면 막는
// 호출이 그것을 '멈춤'으로 보고 곧장 돌아간다.
// 돌려주는 Task 의 history 에는 이번 메시지까지 들어 있다
// (SDK 가 실행 전에 저장소의 history 에 덧붙여 둔다).
func Begin(
	ec *a2asrv.ExecutorContext, yield func(a2a.Event, error) bool,
) (*a2a.Task, *Updater, bool) {
	var task *a2a.Task
	if ec.StoredTask == nil {
		task = a2a.NewSubmittedTask(ec, ec.Message)
	} else {
		task = working(ec.StoredTask, ec.Message)
	}
	return task, NewUpdater(ec, yield), yield(task, nil)
}

// endregion

// region: working
// working 은 Task 를 얕게 복사해 상태만 WORKING 으로 바꾼다.
// Go SDK 는 Task 이벤트를 받은 그대로 저장한다. 그래서 상태를 갈기
// 전에 지난 상태 메시지(되물은 질문)를 이력으로 옮겨 둔다 — SDK 가
// 상태 갱신 때 하는 일(applyStatusUpdate)을 여기서도 해야 질문이
// 이력에서 사라지지 않는다. SDK 가 이번 메시지를 이미 끝에 붙였으면
// 질문은 그 앞에 둔다(물음 → 답의 차례). 같은 messageId 로 다시 온
// 메시지는 SDK 가 붙이지 않으므로 id 가 아니라 같은 값인지로 가린다.
func working(t *a2a.Task, cur *a2a.Message) *a2a.Task {
	c := *t
	if q := t.Status.Message; q != nil {
		h := append([]*a2a.Message(nil), t.History...)
		n := len(h)
		if n > 0 && cur != nil && h[n-1] == cur {
			h = append(h[:n-1], q, h[n-1])
		} else {
			h = append(h, q)
		}
		c.History = h
	}
	c.Status = a2a.TaskStatus{State: a2a.TaskStateWorking}
	return &c
}

// endregion

// Cancel 은 기본 취소: CANCELED 하나를 싣는다(parts 는 알림 글).
func Cancel(
	ec *a2asrv.ExecutorContext, parts ...*a2a.Part,
) iter.Seq2[a2a.Event, error] {
	return func(yield func(a2a.Event, error) bool) {
		NewUpdater(ec, yield).Status(a2a.TaskStateCanceled, parts...)
	}
}

// Sleep 은 ms 만큼 쉰다. 그 사이 취소되면(ctx) false.
func Sleep(ctx context.Context, ms int) bool {
	t := time.NewTimer(time.Duration(ms) * time.Millisecond)
	defer t.Stop()
	select {
	case <-t.C:
		return true
	case <-ctx.Done():
		return false
	}
}
