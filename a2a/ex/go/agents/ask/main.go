// 총무팀의 명령줄 클라이언트.
//
// 에이전트에게 말을 걸고 오가는 것을 찍는다.
//
//	go run ./agents/ask URL [--data JSON] [--token T] 첫말 [답1 답2 …]
//
// 작업이 INPUT_REQUIRED·AUTH_REQUIRED 에서 멈추면 남은 답을 같은
// taskId·contextId 로 차례로 보낸다(대본이 있는 대화). 카드가
// 스트리밍을 지원하면 스트림으로, 아니면 막는 호출로 받는다.
package main

import (
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"iter"
	"maps"
	"math"
	"os"
	"slices"
	"strconv"
	"strings"
	"unicode/utf8"

	"github.com/a2aproject/a2a-go/v2/a2a"
	"github.com/a2aproject/a2a-go/v2/a2aclient"
	"github.com/a2aproject/a2a-go/v2/a2aclient/agentcard"

	"example.com/workshop/agents/common"
)

// region: dump
// dump 은 짧으면 한 줄, 길면 들여 쓴 여러 줄(접힌 폰 화면 폭 때문).
// 파이썬 json.dumps(sort_keys, ensure_ascii=False) 와 같은 글자를
// 내도록 직접 쓴다 — Go 의 json 은 ", "·": " 사이 띄어쓰기가 없다.
func dump(v any) string {
	one := encode(v, -1, 0)
	if utf8.RuneCountInString(one) <= 60 { // 바이트가 아니라 글자 수
		return one
	}
	return encode(v, 1, 0)
}

// encode: indent < 0 이면 한 줄, 아니면 한 단계에 indent 칸씩.
func encode(v any, indent, level int) string {
	var items []string
	open, close := "[", "]"
	switch x := v.(type) {
	case map[string]any:
		open, close = "{", "}"
		for _, k := range slices.Sorted(maps.Keys(x)) {
			items = append(items,
				str(k)+": "+encode(x[k], indent, level+1))
		}
	case []any:
		for _, e := range x {
			items = append(items, encode(e, indent, level+1))
		}
	case float64:
		return num(x)
	case string:
		return str(x)
	default: // bool, nil
		b, _ := json.Marshal(x)
		return string(b)
	}
	if len(items) == 0 {
		return open + close
	}
	if indent < 0 {
		return open + strings.Join(items, ", ") + close
	}
	pad := "\n" + strings.Repeat(" ", indent*(level+1))
	end := "\n" + strings.Repeat(" ", indent*level)
	return open + pad + strings.Join(items, ","+pad) + end + close
}

// endregion

// num: 30.0 처럼 소수부가 없는 실수는 정수로 보인다(4부 참고).
func num(x float64) string {
	if x == math.Trunc(x) && !math.IsInf(x, 0) {
		return strconv.FormatFloat(x, 'f', 0, 64)
	}
	return strconv.FormatFloat(x, 'g', -1, 64)
}

// str 은 JSON 문자열. HTML 문자(<, >, &)를 < 로 바꾸지 않는다.
func str(s string) string {
	var b strings.Builder
	enc := json.NewEncoder(&b)
	enc.SetEscapeHTML(false)
	_ = enc.Encode(s)
	return strings.TrimSuffix(b.String(), "\n")
}

// showParts 는 파트 하나당 한 조각: 글은 그대로, 데이터는 JSON,
// 파일은 크기.
func showParts(parts []*a2a.Part) string {
	var out []string
	for _, p := range parts {
		switch c := p.Content.(type) {
		case a2a.Text:
			out = append(out, strings.TrimRight(string(c), "\n"))
		case a2a.Data:
			out = append(out, dump(c.Value))
		case a2a.Raw:
			name := p.Filename
			if name == "" {
				name = "파일"
			}
			out = append(out,
				fmt.Sprintf("<%s %d바이트>", name, len(c)))
		case a2a.URL:
			out = append(out, "<"+string(c)+">")
		}
	}
	return strings.Join(out, " | ")
}

func stateName(s a2a.TaskState) string {
	return strings.TrimPrefix(string(s), "TASK_STATE_")
}

func msgParts(m *a2a.Message) string {
	if m == nil {
		return ""
	}
	return showParts(m.Parts)
}

func line(format string, a ...any) {
	s := fmt.Sprintf(format, a...)
	fmt.Println(strings.TrimRight(s, " \t\n")) // 파이썬 rstrip()
}

// show 는 이벤트 하나를 한 줄로 찍는다. 작업 이벤트가면 그 작업의
// taskId·contextId·상태를 돌려준다(아티팩트 이벤트의 상태는 빈 값).
func show(ev a2a.Event) (a2a.TaskID, string, a2a.TaskState) {
	switch e := ev.(type) {
	case *a2a.Message:
		fmt.Printf("message: %s\n", showParts(e.Parts))
	case *a2a.Task:
		st := e.Status
		line("task %s %s", stateName(st.State), msgParts(st.Message))
		for _, a := range e.Artifacts {
			fmt.Printf("  artifact %s: %s\n", a.Name,
				showParts(a.Parts))
		}
		return e.ID, e.ContextID, st.State
	case *a2a.TaskStatusUpdateEvent:
		st := e.Status
		line("status %s %s", stateName(st.State), msgParts(st.Message))
		return e.TaskID, e.ContextID, st.State
	case *a2a.TaskArtifactUpdateEvent:
		flags := ""
		if e.Append {
			flags = "+"
		}
		if e.LastChunk {
			flags += " (끝)"
		}
		fmt.Printf("artifact %s%s: %s\n", e.Artifact.Name, flags,
			showParts(e.Artifact.Parts))
		return e.TaskID, e.ContextID, ""
	}
	return "", "", ""
}

// parseArgs 는 플래그와 위치 인자를 섞어 받는다(파이썬 argparse 처럼).
// Go 의 flag 는 첫 위치 인자에서 멈추므로 남은 것을 다시 읽힌다.
func parseArgs() (url string, lines []string, data, token string,
	noStream bool) {
	d := flag.String("data", "", "첫 메시지에 붙일 DataPart(JSON)")
	t := flag.String("token", "", "Bearer 토큰")
	n := flag.Bool("no-stream", false, "막는 호출로만 받는다")
	var pos []string
	rest := os.Args[1:]
	for {
		_ = flag.CommandLine.Parse(rest)
		rest = flag.Args()
		if len(rest) == 0 {
			break
		}
		pos, rest = append(pos, rest[0]), rest[1:]
	}
	if len(pos) == 0 {
		fmt.Fprintln(os.Stderr, "URL 이 필요합니다")
		os.Exit(2)
	}
	return pos[0], pos[1:], *d, *t, *n
}

func main() {
	url, lines, data, token, noStream := parseArgs()
	ctx := context.Background()
	hc := common.HTTPClient(token)
	card, err := agentcard.NewResolver(hc).Resolve(ctx, url)
	check(err)
	client, err := a2aclient.NewFromCard(ctx, card,
		a2aclient.WithJSONRPCTransport(hc))
	check(err)
	defer client.Destroy()
	var parts []*a2a.Part
	if len(lines) > 0 {
		parts = append(parts, a2a.NewTextPart(lines[0]))
		lines = lines[1:]
	}
	if data != "" {
		var v any
		check(json.Unmarshal([]byte(data), &v))
		parts = append(parts, a2a.NewDataPart(v))
	}
	var taskID a2a.TaskID
	var contextID string
	for {
		msg := a2a.NewMessage(a2a.MessageRoleUser, parts...)
		// 대본 안에서 겹치지 않게
		msg.ID = fmt.Sprintf("ask-%d", len(lines))
		msg.TaskID, msg.ContextID = taskID, contextID
		req := &a2a.SendMessageRequest{Message: msg}
		var last a2a.TaskState
		for ev, err := range send(ctx, client, req, noStream) {
			check(err)
			if id, cid, st := show(ev); st != "" {
				taskID, contextID, last = id, cid, st
			}
		}
		paused := last == a2a.TaskStateInputRequired ||
			last == a2a.TaskStateAuthRequired
		if !paused || len(lines) == 0 {
			break
		}
		reply := lines[0]
		lines = lines[1:]
		fmt.Printf("> %s\n", reply)
		parts = []*a2a.Part{a2a.NewTextPart(reply)}
	}
}

// send 는 스트림이든 막는 호출이든 이벤트의 흐름으로 돌려준다.
func send(
	ctx context.Context, c *a2aclient.Client,
	req *a2a.SendMessageRequest, noStream bool,
) iter.Seq2[a2a.Event, error] {
	if !noStream {
		return c.SendStreamingMessage(ctx, req)
	}
	return func(yield func(a2a.Event, error) bool) {
		res, err := c.SendMessage(ctx, req)
		if err != nil {
			yield(nil, err)
			return
		}
		yield(res.(a2a.Event), nil)
	}
}

func check(err error) {
	if err != nil {
		fmt.Fprintln(os.Stderr, "오류:", err)
		os.Exit(1)
	}
}
