// 고치기 전의 맨손 Go 서버가 GetTask 의 인자를 읽던 방법 그대로 —
// json.Unmarshal 의 오류를 버리면 구조체에 무엇이 남는가.
package main

import (
	"encoding/json"
	"fmt"
)

// region: lax
type taskParams struct { // 고치기 전의 모양 — id 는 string
	ID            string `json:"id"`
	HistoryLength *int   `json:"historyLength"`
}

func main() {
	for _, body := range []string{
		`{"id":"t-1","historyLength":2}`,
		`{"historyLength":"2","id":"t-1"}`,
		`{"id":5}`,
	} {
		var p taskParams
		// 고치기 전의 서버는 이 err 를 버렸다
		err := json.Unmarshal([]byte(body), &p)
		hl := "nil"
		if p.HistoryLength != nil {
			hl = fmt.Sprintf("&%d", *p.HistoryLength)
		}
		fmt.Printf("%s\n  id=%q historyLength=%s\n  err: %v\n",
			body, p.ID, hl, err)
	}
}

// endregion
