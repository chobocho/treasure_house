// Message 를 세 길로 만들고, 와이어 모양과 SDK 안의 모양을 본다.
//
//	go run ./09/types_build
package main

import (
	"encoding/json"
	"fmt"
	"reflect"

	"github.com/a2aproject/a2a-go/v2/a2a"
)

func main() {
	// region: build
	// ① 생성 함수 — messageId 는 새 UUID 를 지어 준다
	a := a2a.NewMessage(a2a.MessageRoleUser,
		a2a.NewTextPart("숙소 부탁합니다"))
	a.ID = "m-1" // 견주려고 고정
	// ② 구조체 글자(literal) — 안 적은 필드는 영값("", nil)
	b := &a2a.Message{
		ID:    "m-1",
		Role:  a2a.MessageRoleUser,
		Parts: a2a.ContentParts{{Content: a2a.Text("숙소 부탁합니다")}},
	}
	// ③ 와이어 모양 JSON 을 json.Unmarshal 로
	var c a2a.Message
	err := json.Unmarshal([]byte(`{"messageId":"m-1",
	  "role":"ROLE_USER","parts":[{"text":"숙소 부탁합니다"}]}`), &c)
	fmt.Println("a = b:", reflect.DeepEqual(a, b),
		" b = c:", reflect.DeepEqual(b, &c), " 오류:", err)
	fmt.Printf("Role %q  ContextID %q\n", c.Role, c.ContextID)
	// endregion

	// region: wire
	// json.Marshal 이 곧 와이어 모양 — 빈 필드는 omitempty 로 빠진다
	wire, _ := json.MarshalIndent(b, "", " ")
	fmt.Println("json.Marshal(b):")
	fmt.Println(string(wire))
	// %+v 는 SDK 안의 모양 — Part 는 Content 하나에 타입 하나
	fmt.Printf("%%+v: %+v\n", *b.Parts[0])
	fmt.Printf("%%T: %T\n", b.Parts[0].Content)
	// endregion
}
