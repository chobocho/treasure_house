// 맨손 클라이언트 — net/http 만으로 카드를 읽고, JSON-RPC 인터페이스를
// 골라, 숙소 에이전트와 두 번 이야기한다(막는 호출, 그다음 스트림).
//
//	go run ./06/client 에이전트_주소
package main

import (
	"bufio"
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"iter"
	"net/http"
	"os"
	"strings"
)

// region: types
// 와이어에서 읽을 것만 — 나머지 필드는 Unmarshal 이 버린다.
type part struct {
	Text *string `json:"text"` // 글 파트가 아니면 nil
}
type status struct {
	State   string `json:"state"`
	Message *struct {
		Parts []part `json:"parts"`
	} `json:"message"`
}
type artifact struct {
	Name  string `json:"name"`
	Parts []part `json:"parts"`
}
type ids struct {
	TaskID    string `json:"taskId,omitempty"`
	ContextID string `json:"contextId,omitempty"`
}

// event 는 StreamResponse — 넷 중 하나만 채워진다(oneof).
type event struct {
	Task *struct {
		ID        string     `json:"id"`
		ContextID string     `json:"contextId"`
		Status    status     `json:"status"`
		Artifacts []artifact `json:"artifacts"`
	} `json:"task"`
	Message *struct {
		Parts []part `json:"parts"`
	} `json:"message"`
	StatusUpdate *struct {
		ids
		Status status `json:"status"`
	} `json:"statusUpdate"`
	ArtifactUpdate *struct {
		ids
		Artifact artifact `json:"artifact"`
	} `json:"artifactUpdate"`
}

// endregion

// region: card
type iface struct {
	URL             string `json:"url"`
	ProtocolBinding string `json:"protocolBinding"`
	ProtocolVersion string `json:"protocolVersion"`
	Tenant          string `json:"tenant"`
}
type card struct {
	Name                string  `json:"name"`
	SupportedInterfaces []iface `json:"supportedInterfaces"`
}

// pick: 카드를 받아 JSON-RPC 1.0 인터페이스를 고른다(§8.3.2).
func pick(base string) (card, iface) {
	resp, err := http.Get(strings.TrimSuffix(base, "/") +
		"/.well-known/agent-card.json")
	check(err)
	defer resp.Body.Close()
	var c card
	check(json.NewDecoder(resp.Body).Decode(&c))
	// 앞의 것이 더 바라는 인터페이스다(§8.3.1) — 처음 맞는 것을 쓴다
	for _, i := range c.SupportedInterfaces {
		v := strings.Split(i.ProtocolVersion, ".")
		if i.ProtocolBinding == "JSONRPC" && len(v) >= 2 &&
			v[0] == "1" && v[1] == "0" {
			return c, i
		}
	}
	fmt.Println("쓸 수 있는 인터페이스가 없습니다")
	os.Exit(1)
	return c, iface{}
}

// endregion

// region: rpc
var n = 0 // JSON-RPC id 와 messageId 를 매기는 번호

// rpc: 봉투를 싸서 고른 인터페이스의 url 로 — 판 헤더는 늘(§3.6.1).
func rpc(in iface, method string, params map[string]any,
) *http.Response {
	if in.Tenant != "" { // 카드에 tenant 가 있으면 그대로(§8.3.2)
		params["tenant"] = in.Tenant
	}
	n++
	body, _ := json.Marshal(map[string]any{"jsonrpc": "2.0",
		"id": n, "method": method, "params": params})
	req, err := http.NewRequest("POST", in.URL, bytes.NewReader(body))
	check(err)
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("A2A-Version", "1.0")
	resp, err := http.DefaultClient.Do(req)
	check(err)
	return resp
}

// result: JSON-RPC 응답 → result. 오류면 code·message 를 들고 끝낸다.
func result(data []byte) event {
	var resp struct {
		Result event
		Error  *struct {
			Code    int
			Message string
		}
	}
	check(json.Unmarshal(data, &resp))
	if resp.Error != nil {
		fmt.Printf("오류 %d %s\n", resp.Error.Code, resp.Error.Message)
		os.Exit(1)
	}
	return resp.Result
}

// endregion

// region: message
// msg 는 보낼 Message — 빈 id 는 omitempty 로 빠진다(새 작업).
type msg struct {
	MessageID string `json:"messageId"`
	Role      string `json:"role"`
	ids
	Parts []map[string]string `json:"parts"`
}

// message: 사용자 메시지 — 이어 말하기면 taskId·contextId 를 단다.
func message(text string, to ids) msg {
	n++
	return msg{fmt.Sprintf("c-%d", n), "ROLE_USER", to,
		[]map[string]string{{"text": text}}}
}

func check(err error) {
	if err != nil {
		fmt.Println(err)
		os.Exit(1)
	}
}

// endregion

// region: stream
// sseEvents: 2부의 파서를 줄였다 — data 줄을 모으고, 빈 줄이 끝.
func sseEvents(body io.Reader) iter.Seq[string] {
	return func(yield func(string) bool) {
		sc := bufio.NewScanner(body)
		var data []string
		for sc.Scan() {
			line := sc.Text()
			if line == "" && len(data) > 0 &&
				!yield(strings.Join(data, "\n")) {
				return
			}
			if line == "" {
				data = nil
			} else if v, ok := strings.CutPrefix(line, "data:"); ok {
				data = append(data, strings.TrimPrefix(v, " "))
			}
		}
	}
}

// stream: SendStreamingMessage → StreamResponse 를 하나씩.
func stream(in iface, m msg) iter.Seq[event] {
	return func(yield func(event) bool) {
		resp := rpc(in, "SendStreamingMessage",
			map[string]any{"message": m})
		defer resp.Body.Close()
		ct := resp.Header.Get("Content-Type")
		if !strings.HasPrefix(ct, "text/event-stream") {
			data, _ := io.ReadAll(resp.Body) // 첫 이벤트 전의 오류(5장)
			yield(result(data))
			return
		}
		for data := range sseEvents(resp.Body) {
			if !yield(result([]byte(data))) {
				return
			}
		}
	}
}

// endregion

// region: words
// texts: 글 파트만 이어 붙인다 — 데이터 파트는 건너뛴다.
func texts(parts []part) string {
	var out []string
	for _, p := range parts {
		if p.Text != nil {
			out = append(out, *p.Text)
		}
	}
	return strings.Join(out, " ")
}

func line(words ...string) string {
	var out []string
	for _, w := range words {
		if w != "" {
			out = append(out, w)
		}
	}
	return strings.Join(out, " ")
}

func said(s status) string {
	if s.Message == nil {
		return ""
	}
	return texts(s.Message.Parts)
}

// endregion

// region: show
// show: StreamResponse 하나 → 한 줄과, 이어 말할 때 쓸 두 id.
func show(ev event) (string, ids) {
	switch {
	case ev.Task != nil:
		t := ev.Task
		words := []string{"task", t.Status.State[11:], said(t.Status)}
		for _, a := range t.Artifacts {
			words = append(words, texts(a.Parts))
		}
		return line(words...), ids{t.ID, t.ContextID}
	case ev.StatusUpdate != nil:
		u := ev.StatusUpdate
		return line("statusUpdate", u.Status.State[11:],
			said(u.Status)), u.ids
	case ev.ArtifactUpdate != nil:
		a := ev.ArtifactUpdate
		return "artifactUpdate " + a.Artifact.Name + ": " +
			texts(a.Artifact.Parts), a.ids
	}
	return "message " + texts(ev.Message.Parts), ids{}
}

// endregion

// region: main
// send: SendMessage(막는 호출) → 답 Task 를 한 줄로.
func send(in iface, text string, to ids) (string, ids) {
	resp := rpc(in, "SendMessage",
		map[string]any{"message": message(text, to)})
	defer resp.Body.Close()
	data, err := io.ReadAll(resp.Body)
	check(err)
	return show(result(data))
}

func main() {
	c, in := pick(os.Args[1])
	fmt.Printf("카드: %s → JSONRPC %s\n", c.Name, in.ProtocolVersion)
	line, to := send(in, "2026-10-30 1박", ids{})
	fmt.Println("① SendMessage →", line)
	line, to = send(in, "30명", to) // 같은 작업에 이어 말하기
	fmt.Println("② 이어 말하기 →", line)
	fmt.Println("③ SendStreamingMessage '2026-11-06 1박'")
	for ev := range stream(in, message("2026-11-06 1박", ids{})) {
		line, to = show(ev)
		fmt.Println("  ", line)
	}
	fmt.Println("④ SendStreamingMessage '20명'")
	for ev := range stream(in, message("20명", to)) {
		line, _ = show(ev)
		fmt.Println("  ", line)
	}
}

// endregion
//@ norun
