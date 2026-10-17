// DataPart 의 Value — 넣을 때는 아무 Go 값, 읽으면 JSON 의 기본 타입.
//
//	go run ./09/types_data
package main

import (
	"encoding/json"
	"fmt"

	"github.com/a2aproject/a2a-go/v2/a2a"

	"example.com/workshop/workshop"
)

func main() {
	// region: data
	// 구조체를 그대로 넣는다 — 키는 구조체의 json 태그가 정한다
	req := workshop.LodgingRequest{
		Date: "2026-10-30", Nights: 1, Headcount: 30,
	}
	out := a2a.NewMessage(a2a.MessageRoleUser, a2a.NewDataPart(req))
	wire, _ := json.Marshal(out.Parts[0])
	fmt.Println("와이어:", string(wire))
	// 받는 쪽에서는 map[string]any, 수는 float64 다
	var in a2a.Part
	_ = json.Unmarshal(wire, &in)
	data := in.Data().(map[string]any)
	fmt.Printf("읽은 값: %T, headcount %v (%T)\n",
		data, data["headcount"], data["headcount"])
	// endregion

	// region: kinds
	// Value 에는 객체가 아닌 것도 들어간다 — 와이어에서도 그대로
	for _, v := range []any{[]int{1, 2}, "inn", 3.5, nil} {
		b, _ := json.Marshal(a2a.NewDataPart(v))
		fmt.Printf("%-8s → %s\n", fmt.Sprint(v), b)
	}
	// endregion
}
