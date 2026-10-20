// Client 의 메서드 ↔ JSON-RPC 메서드, 그리고 팩토리의 옵션.
//
//	go run ./09/client_api
package main

import (
	"context"
	"encoding/json"
	"fmt"
	"go/ast"
	"go/types"
	"io"
	"net/http"
	"reflect"
	"strings"

	"github.com/a2aproject/a2a-go/v2/a2a"
	"github.com/a2aproject/a2a-go/v2/a2aclient"

	"example.com/workshop/09/sdksrc"
)

// region: fake
// 가짜 전송 — 요청 본문의 method 만 적고 서버 없이 오류로 답한다.
type fake struct{ last *string }

func (f fake) RoundTrip(r *http.Request) (*http.Response, error) {
	var body struct{ Method string }
	b, _ := io.ReadAll(r.Body)
	json.Unmarshal(b, &body)
	*f.last = body.Method
	return &http.Response{StatusCode: 500, Status: "500",
		Body: io.NopCloser(strings.NewReader(""))}, nil
}

// endregion

func main() {
	ctx := context.Background()
	var last string
	hc := &http.Client{Transport: fake{&last}}
	// region: api
	c, _ := a2aclient.NewFromEndpoints(ctx, []*a2a.AgentInterface{
		a2a.NewAgentInterface("http://agent.invalid/",
			a2a.TransportProtocolJSONRPC),
	}, a2aclient.WithJSONRPCTransport(hc))
	id := a2a.TaskID("t-1")
	m := &a2a.SendMessageRequest{Message: a2a.NewMessage(
		a2a.MessageRoleUser, a2a.NewTextPart("안녕"))}
	g := &a2a.GetTaskRequest{ID: id}
	x := &a2a.CancelTaskRequest{ID: id}
	sub := &a2a.SubscribeToTaskRequest{ID: id}
	pc := &a2a.PushConfig{TaskID: id}
	ls := &a2a.ListTasksRequest{}
	calls := map[string]func(){
		"SendMessage": func() { c.SendMessage(ctx, m) },
		"SendStreamingMessage": func() {
			for range c.SendStreamingMessage(ctx, m) {
			}
		},
		"GetTask":    func() { c.GetTask(ctx, g) },
		"ListTasks":  func() { c.ListTasks(ctx, ls) },
		"CancelTask": func() { c.CancelTask(ctx, x) },
		"SubscribeToTask": func() {
			for range c.SubscribeToTask(ctx, sub) {
			}
		},
		"CreateTaskPushConfig": func() {
			c.CreateTaskPushConfig(ctx, pc)
		},
		"GetTaskPushConfig": func() {
			c.GetTaskPushConfig(ctx, &a2a.GetTaskPushConfigRequest{})
		},
		"ListTaskPushConfigs": func() {
			c.ListTaskPushConfigs(ctx, &a2a.ListTaskPushConfigRequest{})
		},
		"DeleteTaskPushConfig": func() {
			c.DeleteTaskPushConfig(ctx,
				&a2a.DeleteTaskPushConfigRequest{})
		},
		"GetExtendedAgentCard": func() {
			c.GetExtendedAgentCard(ctx,
				&a2a.GetExtendedAgentCardRequest{})
		},
	}
	// endregion
	fmt.Println("*a2aclient.Client 메서드 → 와이어의 method")
	t := reflect.TypeOf(c)
	for i := range t.NumMethod() {
		name := t.Method(i).Name
		call, ok := calls[name]
		if !ok {
			fmt.Printf("  %-22s (와이어 없음)\n", name)
			continue
		}
		last = ""
		call()
		fmt.Printf("  %-22s → %s\n", name, last)
	}
	options()
}

// options 는 FactoryOption 을 돌려주는 함수를 소스에서 찾는다.
func options() {
	_, files := sdksrc.Parse(sdksrc.Dir(), "a2aclient")
	fmt.Println("a2aclient.NewFromCard(ctx, card, 옵션...) 의 옵션")
	for _, f := range files {
		for _, d := range f.Decls {
			fn, ok := d.(*ast.FuncDecl)
			if !ok || fn.Recv != nil || fn.Type.Results == nil {
				continue
			}
			res := types.ExprString(fn.Type.Results.List[0].Type)
			if res != "FactoryOption" {
				continue
			}
			var ps []string
			for _, p := range fn.Type.Params.List {
				ps = append(ps, types.ExprString(p.Type))
			}
			fmt.Printf("  %s(%s)\n", fn.Name.Name,
				strings.Join(ps, ", "))
		}
	}
}
