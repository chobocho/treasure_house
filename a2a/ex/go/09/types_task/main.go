// Task 를 짓고(에이전트 쪽), 받은 JSON 에서 읽는다(클라이언트 쪽).
//
//	go run ./09/types_task
package main

import (
	"encoding/json"
	"fmt"
	"maps"
	"slices"

	"github.com/a2aproject/a2a-go/v2/a2a"
)

func main() {
	msg := &a2a.Message{ID: "m-1", Role: a2a.MessageRoleUser,
		Parts: a2a.ContentParts{a2a.NewTextPart("30명")}}

	// region: make
	// 첫 인자는 TaskInfoProvider — id 둘을 알려 주는 무엇이든
	info := a2a.TaskInfo{TaskID: "t-1", ContextID: "c-1"}
	task := a2a.NewSubmittedTask(info, msg)
	b, _ := json.Marshal(task)
	fmt.Println("새 Task:", string(b))
	// id 를 비워 주면 새로 짓는다 — UUID 의 판(version)은 7
	auto := a2a.NewSubmittedTask(a2a.TaskInfo{}, msg)
	fmt.Printf("지은 id 의 판: %c, contextId 의 판: %c\n",
		auto.ID[14], auto.ContextID[14])
	// endregion

	// region: read
	body := `{"id":"t-1","contextId":"c-1",
	  "status":{"state":"TASK_STATE_COMPLETED"},
	  "createdAt":"2026-10-17T00:00:00Z",
	  "artifacts":[{"artifactId":"a-1",
	    "parts":[{"raw":"7JWI64WV","mediaType":"text/plain"}]}]}`
	var got a2a.Task // 모르는 키(createdAt)는 버린다
	err := json.Unmarshal([]byte(body), &got)
	fmt.Println("상태:", got.Status.State, " 오류:", err)
	p := got.Artifacts[0].Parts[0]
	fmt.Println("raw:", string(p.Raw()), p.MediaType)
	// endregion

	// region: stream
	// 스트림의 한 칸 — Event 를 감싸면 와이어 키 하나가 된다
	ev, _ := json.Marshal(a2a.StreamResponse{Event: &got})
	var keys map[string]any
	_ = json.Unmarshal(ev, &keys)
	fmt.Println("StreamResponse 와이어:",
		slices.Sorted(maps.Keys(keys)))
	// endregion
}
