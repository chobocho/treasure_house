// 클라이언트 쪽에서 오류는 어떤 값으로 오나.
//
//	go run ./09/client_errors URL DEAD_URL
//
// URL 은 숙소 에이전트, DEAD_URL 은 아무도 듣지 않는 주소다.
package main

import (
	"context"
	"errors"
	"fmt"
	"os"
	"strings"
	"syscall"

	"github.com/a2aproject/a2a-go/v2/a2a"
	"github.com/a2aproject/a2a-go/v2/a2aclient"
	"github.com/a2aproject/a2a-go/v2/a2aclient/agentcard"
)

// region: report
// report 는 오류의 겉 타입, 우리가 가를 수 있는 것, 첫 줄을 찍는다.
func report(label string, err error) {
	var a2aErr *a2a.Error
	var status *agentcard.ErrStatusNotOK
	fmt.Printf("%s: %T\n", label, err)
	switch {
	case errors.As(err, &status):
		fmt.Printf("    errors.As *agentcard.ErrStatusNotOK %d\n",
			status.StatusCode)
	case errors.Is(err, a2a.ErrTaskNotFound):
		errors.As(err, &a2aErr)
		fmt.Println("    errors.Is a2a.ErrTaskNotFound —", a2aErr.Err)
	case errors.Is(err, syscall.ECONNREFUSED):
		fmt.Println("    errors.Is syscall.ECONNREFUSED")
	default:
		fmt.Println("    가를 것 없음 — 글뿐")
	}
	line, _, _ := strings.Cut(err.Error(), "\n")
	if r := []rune(line); len(r) > 90 {
		line = string(r[:90]) + "…"
	}
	fmt.Println("   ", line)
}

// endregion

func main() {
	url, dead := os.Args[1], os.Args[2]
	ctx := context.Background()
	r := agentcard.DefaultResolver
	// region: errors
	_, err := r.Resolve(ctx, dead) // ① 카드를 받을 수 없다
	report("① 닿지 않는 카드", err)
	_, err = r.Resolve(ctx, url+"nothing/") // ② 카드 경로가 404
	report("② 없는 카드", err)
	card, _ := r.Resolve(ctx, url)
	client, _ := a2aclient.NewFromCard(ctx, card)
	_, err = client.GetTask(ctx, &a2a.GetTaskRequest{ID: "t-없음"})
	report("③ 없는 작업", err) // JSON-RPC 오류
	// 인터페이스 url 만 틀리게 고친 사본
	bad := *card
	iface := *card.SupportedInterfaces[0]
	iface.URL = url + "rpc"
	bad.SupportedInterfaces = []*a2a.AgentInterface{&iface}
	wrong, _ := a2aclient.NewFromCard(ctx, &bad)
	m := a2a.NewMessage(a2a.MessageRoleUser, a2a.NewTextPart("숙소"))
	_, err = wrong.SendMessage(ctx, &a2a.SendMessageRequest{Message: m})
	report("④ 틀린 url", err) // 404
	// endregion
}

//@ norun
