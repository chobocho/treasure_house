// JSON-RPC 2.0 요청 하나를 표준 라이브러리만으로 만든다.
package main

import (
	"encoding/json"
	"fmt"
)

// region: types
// map 은 키를 정렬해 버리므로 순서를 지키려고 구조체를 쓴다.
type Part struct {
	Text string `json:"text"`
}

type Message struct {
	Role      string `json:"role"`
	MessageID string `json:"messageId"`
	Parts     []Part `json:"parts"`
}

type Params struct {
	Message Message `json:"message"`
}

type Request struct {
	JSONRPC string `json:"jsonrpc"`
	ID      int    `json:"id"`
	Method  string `json:"method"`
	Params  Params `json:"params"`
}

// endregion

func main() {
	req := Request{
		JSONRPC: "2.0",
		ID:      1,
		Method:  "SendMessage",
		Params: Params{Message: Message{
			Role:      "ROLE_USER",
			MessageID: "msg-1",
			Parts:     []Part{{Text: "1박 2일, 30명"}},
		}},
	}
	out, err := json.MarshalIndent(req, "", "  ")
	if err != nil {
		panic(err)
	}
	fmt.Println(string(out))
}
