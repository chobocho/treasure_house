// JSON-RPC 2.0 서버 — net/http 와 encoding/json 만으로. 메서드는 하나,
// ChooseLodging(숙소 고르기). 알림과 배치까지 JSON-RPC 2.0 대로.
package main

import (
	"bytes"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"net/http"

	"example.com/workshop/workshop"
)

// region: types
type Request struct {
	JSONRPC string          `json:"jsonrpc"`
	ID      json.RawMessage `json:"id"` // 없으면 nil — 알림
	Method  string          `json:"method"`
	Params  json.RawMessage `json:"params"`
}

type Error struct {
	Code    int    `json:"code"`
	Message string `json:"message"`
}

// id 는 받은 글자 그대로 돌려준다. nil 이면 null 로 나간다.
type Response struct {
	JSONRPC string          `json:"jsonrpc"`
	ID      json.RawMessage `json:"id"`
	Result  any             `json:"result,omitempty"`
	Error   *Error          `json:"error,omitempty"`
}

func fail(id json.RawMessage, code int, msg string) *Response {
	return &Response{"2.0", id, nil, &Error{code, msg}}
}

// endregion

// region: call
// 정수 필드가 포인터라 빠진 것(nil)과 0 을 가른다.
type lodgingParams struct {
	Date      *string `json:"date"`
	Nights    *int    `json:"nights"`
	Headcount *int    `json:"headcount"`
}

// 요청 하나 → 응답. 알림(id 없음)이면 nil.
func call(raw json.RawMessage) *Response {
	var req Request
	if json.Unmarshal(raw, &req) != nil || req.JSONRPC != "2.0" ||
		req.Method == "" {
		return fail(nil, -32600, "Invalid Request")
	}
	var resp *Response
	var p lodgingParams
	switch {
	case req.Method != "ChooseLodging":
		resp = fail(req.ID, -32601, "Method not found")
	case json.Unmarshal(req.Params, &p) != nil || p.Date == nil ||
		p.Nights == nil || p.Headcount == nil:
		resp = fail(req.ID, -32602, "Invalid params")
	default:
		q, f := workshop.ChooseLodging(workshop.LodgingRequest{
			Date: *p.Date, Nights: *p.Nights, Headcount: *p.Headcount})
		var result any = q
		if f != nil { // 업무 실패도 답(result)이다
			result = f
		}
		resp = &Response{JSONRPC: "2.0", ID: req.ID, Result: result}
	}
	if req.ID == nil {
		fmt.Printf("%s 알림 → 응답 안 함\n", req.Method)
		return nil
	}
	outcome := "result"
	if resp.Error != nil {
		outcome = fmt.Sprint(resp.Error.Code)
	}
	fmt.Printf("%s id=%s → %s\n", req.Method, req.ID, outcome)
	return resp
}

// endregion

// region: handle
// HTTP 본문 → 응답(객체·배열) 또는 nil(보낼 것이 없음).
func handle(body []byte) any {
	if !json.Valid(body) {
		return fail(nil, -32700, "Parse error")
	}
	body = bytes.TrimSpace(body)
	if body[0] != '[' {
		if r := call(body); r != nil {
			return r
		}
		return nil
	}
	var batch []json.RawMessage
	json.Unmarshal(body, &batch)
	if len(batch) == 0 { // 빈 배치는 그 자체가 틀린 요청
		return fail(nil, -32600, "Invalid Request")
	}
	out := []*Response{}
	for _, raw := range batch {
		if r := call(raw); r != nil {
			out = append(out, r)
		}
	}
	if len(out) == 0 { // 전부 알림이면 빈 배열이 아니라 무응답
		return nil
	}
	return out
}

func serve(w http.ResponseWriter, r *http.Request) {
	body, _ := io.ReadAll(r.Body)
	resp := handle(body)
	if resp == nil {
		w.WriteHeader(http.StatusNoContent) // 본문 없음
		return
	}
	data, _ := json.Marshal(resp)
	w.Header().Set("Content-Type", "application/json")
	w.Write(data)
}

// endregion

func main() {
	port := flag.Int("port", 0, "들을 포트")
	flag.Parse()
	addr := fmt.Sprintf("127.0.0.1:%d", *port)
	fmt.Println("JSON-RPC 서버(go):", addr)
	http.ListenAndServe(addr, http.HandlerFunc(serve))
}

//@ norun
