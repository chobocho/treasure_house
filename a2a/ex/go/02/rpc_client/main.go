// JSON-RPC 2.0 클라이언트 — net/http 만으로. 요청마다 새 id 를 붙이고,
// 응답의 id 가 맞는지, result 인지 error 인지 가른다.
package main

import (
	"bytes"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"net/http"
)

// region: client
type RPCError struct {
	Code    int    `json:"code"`
	Message string `json:"message"`
}

func (e *RPCError) Error() string {
	return fmt.Sprintf("%d %s", e.Code, e.Message)
}

var lastID = 0

// result 에는 답을 채울 그릇을 넘긴다.
func call(url, method string, params, result any) error {
	lastID++
	body, _ := json.Marshal(map[string]any{"jsonrpc": "2.0",
		"id": lastID, "method": method, "params": params})
	resp, err := http.Post(url, "application/json",
		bytes.NewReader(body))
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	var reply struct {
		ID     int             `json:"id"`
		Result json.RawMessage `json:"result"`
		Error  *RPCError       `json:"error"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&reply); err != nil {
		return err
	}
	if reply.ID != lastID { // 다른 요청의 답이면 받지 않는다
		return fmt.Errorf("id 가 다르다: %d", reply.ID)
	}
	if reply.Error != nil {
		return reply.Error
	}
	return json.Unmarshal(reply.Result, result)
}

// endregion

// region: main
type Quote struct {
	VenueName string `json:"venueName"`
	Rooms     int    `json:"rooms"`
	Total     int    `json:"total"`
}

func main() {
	url := flag.String("url", "", "서버 주소")
	flag.Parse()
	Q := map[string]any{
		"date": "2026-10-30", "nights": 1, "headcount": 30,
	}
	var q Quote
	if err := call(*url, "ChooseLodging", Q, &q); err != nil {
		panic(err)
	}
	fmt.Printf("ChooseLodging → %s %d실 %d원\n",
		q.VenueName, q.Rooms, q.Total)
	var rpcErr *RPCError
	err := call(*url, "BookLodging", Q, &q)
	if errors.As(err, &rpcErr) {
		fmt.Println("BookLodging → 오류", rpcErr)
	}
}

// endregion
//@ norun
