// panic 하는 실행기에 SDK 클라이언트로 묻는다 — 답의 오류를 본다.
//
//	go run ./09/panic_probe BASE
package main

import (
	"context"
	"errors"
	"fmt"
	"os"
	"strings"

	"github.com/a2aproject/a2a-go/v2/a2a"
	"github.com/a2aproject/a2a-go/v2/a2aclient"
)

// region: probe
func main() {
	ctx := context.Background()
	for _, path := range []string{"/panic", "/panic2", "/panic"} {
		c, _ := a2aclient.NewFromEndpoints(ctx, []*a2a.AgentInterface{
			a2a.NewAgentInterface(os.Args[1]+path,
				a2a.TransportProtocolJSONRPC)})
		m := a2a.NewMessage(a2a.MessageRoleUser,
			a2a.NewTextPart("숙소 부탁합니다"))
		req := &a2a.SendMessageRequest{Message: m}
		_, err := c.SendMessage(ctx, req)
		msg := err.Error()
		first, _, _ := strings.Cut(msg, "\n")
		fmt.Printf("%-8s -32603=%v %q\n", path,
			errors.Is(err, a2a.ErrInternalError), first)
		// 스택은 주소가 실행마다 달라 줄 수와 표지만 센다
		fmt.Printf("         %d줄, goroutine 스택=%v\n",
			strings.Count(msg, "\n")+1,
			strings.Contains(msg, "goroutine "))
	}
}

// endregion

//@ norun
