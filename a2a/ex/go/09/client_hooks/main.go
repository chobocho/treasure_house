// 갈고리 둘 — 우리 http.Client 와 호출 가로채기(CallInterceptor).
//
//	go run ./09/client_hooks URL
package main

import (
	"context"
	"fmt"
	"net/http"
	"os"
	"slices"
	"strings"

	"github.com/a2aproject/a2a-go/v2/a2a"
	"github.com/a2aproject/a2a-go/v2/a2aclient"
	"github.com/a2aproject/a2a-go/v2/a2aclient/agentcard"
)

// region: transport
// 우리 RoundTripper — 전송이 실제로 보내는 머리글을 본다.
type peek struct{}

func (peek) RoundTrip(r *http.Request) (*http.Response, error) {
	v := slices.Sorted(slices.Values(r.Header.Values("A2A-Version")))
	fmt.Printf("  http A2A-Version=%q X-Workshop-Team=%q\n",
		v, r.Header.Get("X-Workshop-Team"))
	return http.DefaultTransport.RoundTrip(r)
}

// endregion

// region: interceptor
// 모든 호출의 앞뒤 — 머리글 하나를 더하고, 답의 타입을 본다.
type team struct {
	a2aclient.PassthroughInterceptor
}

func (team) Before(ctx context.Context, req *a2aclient.Request,
) (context.Context, any, error) {
	fmt.Printf("  before %s 판=%q\n", req.Method,
		req.ServiceParams.Get(a2a.SvcParamVersion))
	req.ServiceParams.Append("X-Workshop-Team", "general-affairs")
	return ctx, nil, nil
}

func (team) After(ctx context.Context, resp *a2aclient.Response) error {
	fmt.Printf("  after  %s → %T\n", resp.Method, resp.Payload)
	return nil
}

// endregion

// region: main
func main() {
	ctx := context.Background()
	card, err := agentcard.DefaultResolver.Resolve(ctx, os.Args[1])
	if err != nil {
		panic(err)
	}
	hc := &http.Client{Transport: peek{}}
	client, err := a2aclient.NewFromCard(ctx, card,
		a2aclient.WithJSONRPCTransport(hc),
		a2aclient.WithCallInterceptors(team{}))
	if err != nil {
		panic(err)
	}
	defer client.Destroy()
	// 이 호출에만 붙이는 머리글 — 판을 손으로 0.3 이라고 적어 본다
	call := a2aclient.AttachServiceParams(ctx,
		a2aclient.ServiceParams{"A2A-Version": {"0.3"}})
	m := a2a.NewMessage(a2a.MessageRoleUser,
		a2a.NewTextPart("누구세요"))
	res, err := client.SendMessage(call, &a2a.SendMessageRequest{
		Message: m})
	if err != nil {
		panic(err)
	}
	for _, p := range res.(*a2a.Message).Parts {
		// 서버가 본 판 값 둘은 실행마다 차례가 달라 빼고 찍는다
		// (같은 값은 위 http 줄에 정렬해 찍었다)
		if !strings.HasPrefix(p.Text(), "A2A-Version=") {
			fmt.Printf("  답: %s\n", p.Text())
		}
	}
}

// endregion

//@ norun
