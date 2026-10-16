// 교통 견적 요청을 JSON 으로 쓰고 다시 읽는다 — encoding/json.
package main

import (
	"encoding/json"
	"fmt"
)

// region: roundtrip
// 필드 이름은 대문자로 시작해야 밖(json 패키지)에서 보인다.
// JSON 의 camelCase 이름은 태그로 따로 적는다.
type BusRequest struct {
	Headcount int    `json:"headcount"`
	Nights    int    `json:"nights"`
	Depart    string `json:"depart"`
}

type NoTags struct { // 태그가 없으면 Go 이름 그대로 나간다
	Headcount, Nights int
	Depart            string
}

func main() {
	req := BusRequest{Headcount: 30, Nights: 1, Depart: "강남역"}
	text, _ := json.Marshal(req)
	fmt.Println("쓰기    :", string(text))
	raw, _ := json.Marshal(NoTags{30, 1, "강남역"})
	fmt.Println("태그없음:", string(raw))
	m, _ := json.Marshal(map[string]any{
		"headcount": 30, "nights": 1, "depart": "강남역"})
	fmt.Println("map     :", string(m)) // 키를 정렬해 쓴다

	var back BusRequest // 읽을 모양을 먼저 정해 두고 채운다
	if err := json.Unmarshal(text, &back); err != nil {
		panic(err)
	}
	fmt.Printf("되읽기  : %T %s\n", back, back.Depart)
	fmt.Printf("인원    : %d %T\n", back.Headcount, back.Headcount)
}

// endregion
