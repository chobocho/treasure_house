// Go SDK 가 작업 상태에 찍는 시각을 JSON 으로 적으면 어느 시간대가
// 붙는가 — 서버 프로세스의 지역 시간대(time.Local)를 바꿔 가며 본다.
package main

import (
	"encoding/json"
	"fmt"
	"strings"
	"time"

	"github.com/a2aproject/a2a-go/v2/a2a"
)

// region: stamp
// stamp 는 SDK 가 만든 상태 갱신의 timestamp 를 JSON 문자열로 꺼낸다.
func stamp() string {
	task := &a2a.Task{ID: "t-1", ContextID: "c-1"}
	ev := a2a.NewStatusUpdateEvent(task, a2a.TaskStateWorking, nil)
	b, _ := json.Marshal(ev.Status) // time.Now() 를 그대로 적는다
	var s struct {
		Timestamp string `json:"timestamp"`
	}
	json.Unmarshal(b, &s)
	return s.Timestamp
}

// zone 은 시각의 끝, 시간대 부분만(값은 실행마다 다르다).
func zone(ts string) string {
	if strings.HasSuffix(ts, "Z") {
		return "Z"
	}
	return ts[len(ts)-6:]
}

func main() {
	name, _ := time.Now().Zone()
	fmt.Println("이 기계의 시간대", name, "→", zone(stamp()))
	time.Local = time.FixedZone("KST", 9*60*60) // 서울에 둔 서버라면
	name, _ = time.Now().Zone()
	fmt.Println("이 기계의 시간대", name, "→", zone(stamp()))
}

// endregion
