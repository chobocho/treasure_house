// 파이썬 SDK 가 보낸 DataPart 를 Go 가 정수 칸(int)으로 읽는 두 길.
package main

import (
	"encoding/json"
	"fmt"

	"github.com/a2aproject/a2a-go/v2/a2a"
)

type lodgingRequest struct {
	Date      string `json:"date"`
	Nights    int    `json:"nights"`
	Headcount int    `json:"headcount"`
}

// region: decode
// 파이썬 클라이언트가 와이어에 적은 파트
// (data 명세의 탭 기록과 같은 값)
const wire = `{"data": {"date": "2026-10-30",
	"headcount": 30.0, "nights": 1.0}}`

func main() {
	// ① 바이트를 곧장 구조체로 — int 칸이 30.0 을 거절한다
	var direct struct {
		Data lodgingRequest `json:"data"`
	}
	err := json.Unmarshal([]byte(wire), &direct)
	fmt.Println("① 곧장:", err)

	// ② SDK 의 길 — a2a.Part 의 Data 는 any, 수는 float64 가 된다
	var p a2a.Part
	if err := json.Unmarshal([]byte(wire), &p); err != nil {
		panic(err)
	}
	m := p.Data().(map[string]any)
	h := m["headcount"]
	fmt.Printf("② Part: headcount %T %v\n", h, h)

	// ③ 그 값을 다시 JSON 으로 — float64 30 은 "30" 으로 적힌다
	b, _ := json.Marshal(m)
	var req lodgingRequest
	err = json.Unmarshal(b, &req)
	fmt.Printf("③ 다시: %s → %+v, 오류 %v\n", b, req, err)
}

// endregion
