// 맨손 저장소의 전이 표 시험 — 작업 하나를 만들어 이리저리 옮겨 본다.
package main

import (
	"fmt"
	"strings"

	bs "example.com/workshop/06/barestore"
)

var store = bs.New()
var task = store.Create(bs.Message{MessageID: "m1", Role: "ROLE_USER",
	Parts: []bs.Part{{"text": "2026-10-30 1박 숙소"}}})

func short(state string) string {
	return strings.TrimPrefix(state, "TASK_STATE_")
}

func show() {
	var roles []string
	for _, m := range task.History {
		roles = append(roles, strings.TrimPrefix(m.Role, "ROLE_"))
	}
	state := short(task.Status.State)
	fmt.Printf("   지금 %s, 이력 %s\n", state, strings.Join(roles, " "))
}

// region: try
func attempt(state string, parts ...bs.Part) {
	_, err := bs.Move(task, state, parts...)
	if err != nil { // 오류는 bs.IllegalMove 하나뿐이다
		fmt.Printf("%14s 거부 — %v\n", short(state), err)
		return
	}
	fmt.Printf("%14s 옮김\n", short(state))
	show()
}

func main() {
	show()
	attempt(bs.InputRequired, bs.Part{"text": "인원은 몇 명입니까?"})
	attempt(bs.Completed) // 답을 듣기 전에 끝낼 수는 없다
	attempt(bs.Working)   // 답이 왔다 — 물음은 이력으로
	store.Append(task, bs.Message{MessageID: "m2", Role: "ROLE_USER"})
	show()
	attempt(bs.Submitted) // 뒤로 가지 않는다
	attempt(bs.Completed)
	attempt(bs.Working) // 종료 뒤에는 나갈 곳이 없다
	attempt(bs.Canceled)
}

// endregion
