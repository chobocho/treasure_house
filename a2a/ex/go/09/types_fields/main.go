// 포인터와 값 — 이력에 넣은 메시지, 구조체 복사, 깊은 사본.
//
//	go run ./09/types_fields
package main

import (
	"encoding/json"
	"fmt"

	"github.com/a2aproject/a2a-go/v2/a2a"
)

func main() {
	task := &a2a.Task{ID: "t-1", ContextID: "c-1"}

	// region: assign
	// History 는 []*Message — 넣는 것은 포인터다
	msg := a2a.NewMessage(a2a.MessageRoleUser, a2a.NewTextPart("30명"))
	task.History = append(task.History, msg)
	msg.Parts[0] = a2a.NewTextPart("40명") // 넣은 뒤에 고친다
	fmt.Println("이력의 말:", task.History[0].Parts[0].Text())
	// Status 는 값(TaskStatus) — 통째로 대입한다
	task.Status = a2a.TaskStatus{State: a2a.TaskStateWorking}
	// endregion

	// region: copy
	// 구조체 복사(*task)는 겉만 — 슬라이스는 같은 배열을 본다
	shallow := *task
	shallow.Status.State = a2a.TaskStateCompleted
	shallow.History[0].Role = a2a.MessageRoleAgent
	fmt.Println("원본 상태:", task.Status.State,
		" 원본 역할:", task.History[0].Role)
	// 깊은 사본은 공개 API 에 없다 — JSON 왕복이 손쉬운 길
	var deep a2a.Task
	raw, _ := json.Marshal(task)
	_ = json.Unmarshal(raw, &deep)
	deep.History[0].Parts[0] = a2a.NewTextPart("50명")
	fmt.Println("깊은 사본을 고친 뒤 원본:",
		task.History[0].Parts[0].Text())
	// endregion
}
