// "없음" 의 모양과, json.Unmarshal 이 받아 주는 것·거절하는 것.
//
//	go run ./09/types_presence
package main

import (
	"bytes"
	"encoding/json"
	"fmt"

	"github.com/a2aproject/a2a-go/v2/a2a"
)

func main() {
	// region: presence
	var m a2a.Message
	_ = json.Unmarshal([]byte(`{"messageId":"m-1",
	  "role":"ROLE_USER","parts":[{"text":"30명"}]}`), &m)
	fmt.Printf("contextId %q  metadata %v (nil? %v)\n",
		m.ContextID, m.Metadata, m.Metadata == nil)
	// 영값을 내보내면 — omitempty 가 없는 필드는 남는다
	empty, _ := json.Marshal(a2a.Message{})
	fmt.Println("Message{}:", string(empty))
	task, _ := json.Marshal(a2a.Task{})
	fmt.Println("Task{}:", string(task))
	for _, body := range []string{`{"id":"t-1"}`,
		`{"id":"t-1","historyLength":0}`} {
		var q a2a.GetTaskRequest
		_ = json.Unmarshal([]byte(body), &q)
		fmt.Printf("%s → HistoryLength nil? %v\n", body,
			q.HistoryLength == nil)
	}
	// endregion

	// region: oneof
	for _, body := range []string{
		`{"text":"글","url":"https://x.example/a"}`,
		`{}`, `{"data":null}`, `{"url":""}`,
	} {
		var p a2a.Part
		err := json.Unmarshal([]byte(body), &p)
		fmt.Printf("Part %s → %v\n", body, err)
	}
	// endregion

	// region: enum
	var t a2a.Task
	err := json.Unmarshal([]byte(
		`{"id":"t-1","status":{"state":"TASK_STATE_DONE"}}`), &t)
	fmt.Printf("모르는 상태 → %q, 오류 %v\n", t.Status.State, err)
	// 키는 대소문자를 가리지 않고 맞춘다 — snake_case 는 못 맞춘다
	var k a2a.Message
	_ = json.Unmarshal([]byte(
		`{"MESSAGEID":"m-9","task_id":"t-9","x":1}`), &k)
	fmt.Printf("MESSAGEID → %q, task_id → %q\n", k.ID, k.TaskID)
	// 모르는 키("x")를 오류로 보려면 Decoder 의 스위치를 켠다
	dec := json.NewDecoder(bytes.NewReader([]byte(`{"x":1}`)))
	dec.DisallowUnknownFields()
	fmt.Println("DisallowUnknownFields →", dec.Decode(&k))
	// endregion
}
