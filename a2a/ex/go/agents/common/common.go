// Package common 은 다섯 에이전트가 함께 쓰는 SDK 접착 코드다.
//
// 업무 규칙은 workshop 패키지에 있고, 여기는 A2A 쪽 잔일만 한다:
// 명령줄 읽기, 카드의 공통 부분, 파트 만들기·꺼내기, 서버 띄우기.
package common

import (
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"strconv"
	"strings"

	"github.com/a2aproject/a2a-go/v2/a2a"
)

var Provider = &a2a.AgentProvider{
	Org: "보물상사", URL: "https://treasure-house.example",
}

// Args 는 모든 에이전트가 받는 두 옵션이다.
type Args struct {
	Port int
	URL  string
}

// ParseArgs: --port 는 붙을 곳, --url 은 카드에 적을 바깥 주소.
// 에이전트마다 더 받는 옵션은 부르기 전에 flag 로 등록해 둔다.
func ParseArgs(description string) Args {
	port := flag.Int("port", 0, "붙을 포트(필수)")
	url := flag.String("url", "", "카드에 적을 주소(기본: 붙는 주소)")
	flag.Usage = func() {
		fmt.Fprintln(flag.CommandLine.Output(), description)
		flag.PrintDefaults()
	}
	flag.Parse()
	if *port == 0 {
		fmt.Fprintln(os.Stderr, "--port 가 필요합니다")
		os.Exit(2)
	}
	if *url == "" {
		*url = fmt.Sprintf("http://127.0.0.1:%d/", *port)
	}
	return Args{Port: *port, URL: *url}
}

func JSONRPCInterface(url string) []*a2a.AgentInterface {
	return []*a2a.AgentInterface{
		a2a.NewAgentInterface(url, a2a.TransportProtocolJSONRPC),
	}
}

// Comma: 1234567 → "1,234,567" (파이썬의 f"{n:,}" 와 같은 모양)
func Comma(n int) string {
	s := strconv.Itoa(n)
	if n < 0 {
		return "-" + Comma(-n)
	}
	for i := len(s) - 3; i > 0; i -= 3 {
		s = s[:i] + "," + s[i:]
	}
	return s
}

// Plain 은 구조체를 JSON 그대로의 모양(map·[]any·float64)으로 바꾼다.
// SDK 의 작업 저장소는 gob 으로 깊은 복사를 하는데, 등록하지 않은
// 구조체가 DataPart 에 들어 있으면 복사에 실패하기 때문이다.
func Plain(v any) any {
	b, err := json.Marshal(v)
	if err != nil {
		panic(err)
	}
	var out any
	if err := json.Unmarshal(b, &out); err != nil {
		panic(err)
	}
	return out
}

func TextPart(text string) *a2a.Part { return a2a.NewTextPart(text) }

func DataPart(v any) *a2a.Part { return a2a.NewDataPart(Plain(v)) }

// TextOf 는 글 파트만 줄바꿈으로 이어 붙인다
// (파이썬 get_message_text 와 같게).
func TextOf(m *a2a.Message) string {
	if m == nil {
		return ""
	}
	var texts []string
	for _, p := range m.Parts {
		if t, ok := p.Content.(a2a.Text); ok {
			texts = append(texts, string(t))
		}
	}
	return strings.Join(texts, "\n")
}

// DataOf 는 메시지들의 DataPart 를 앞에서부터 차례로 덮어 합친다.
func DataOf(messages ...*a2a.Message) map[string]any {
	merged := map[string]any{}
	for _, m := range messages {
		if m == nil {
			continue
		}
		for _, p := range m.Parts {
			if d, ok := p.Data().(map[string]any); ok {
				for k, v := range d {
					merged[k] = v
				}
			}
		}
	}
	return merged
}

// Int 는 JSON 숫자를 정수로 읽는다. 파이썬 쪽은 30 을 30.0 으로
// 보내므로(protobuf Value 는 실수뿐이다) 정수 칸으로 바로 풀면
// 실패한다 — 그래서 float64 로 받아 바꾼다. 되물음의 글('30명')
// 에서 온 "30" 같은 문자열도 받는다.
func Int(v any) int {
	switch n := v.(type) {
	case float64:
		return int(n)
	case int:
		return n
	case string:
		i, _ := strconv.Atoi(n)
		return i
	}
	return 0
}

// PyList 는 문자열 목록을 파이썬 repr 모양(['a', 'b'])으로 쓴다.
// 서버 로그 줄을 세 언어가 똑같이 찍기 위해서다.
func PyList(xs []string) string {
	q := make([]string, len(xs))
	for i, x := range xs {
		q[i] = "'" + x + "'"
	}
	return "[" + strings.Join(q, ", ") + "]"
}
