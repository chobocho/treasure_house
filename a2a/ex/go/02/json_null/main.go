// null 과 빠진 필드 — 식사 요청의 caps(끼니별 상한)는 넣어도 빼도 된다.
package main

import (
	"encoding/json"
	"fmt"
)

// region: null
type MealsRequest struct {
	Headcount   int            `json:"headcount"`
	Vegetarians int            `json:"vegetarians,omitempty"`
	Caps        map[string]int `json:"caps"`
}

func main() {
	cases := [][2]string{
		{"caps 빠짐", `{"headcount":30,"vegetarians":2}`},
		{"caps null", `{"headcount":30,"vegetarians":2,"caps":null}`},
		{"채식 0명", `{"headcount":30,"vegetarians":0}`},
	}
	for _, c := range cases {
		var r MealsRequest // 빠져도 null 이어도 영값(nil·0)이다
		json.Unmarshal([]byte(c[1]), &r)
		fmt.Printf("[%s] caps=%v nil=%v vegetarians=%d\n",
			c[0], r.Caps, r.Caps == nil, r.Vegetarians)
	}

	// 쓸 때: nil 맵은 null, omitempty 인 0 은 아예 사라진다
	out, _ := json.Marshal(MealsRequest{Headcount: 30})
	fmt.Println("영값 쓰기 :", string(out))
}

// endregion
