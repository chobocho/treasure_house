// HTTP 요청의 무엇이 실행기까지 오나 — 받은 것을 파트로 돌려준다.
//
//	go run ./09/headers --port P
package main

import (
	"context"
	"flag"
	"fmt"
	"iter"
	"net/http"
	"os"

	"github.com/a2aproject/a2a-go/v2/a2a"
	"github.com/a2aproject/a2a-go/v2/a2asrv"

	"example.com/workshop/09/steps"
)

// region: executor
func who(
	ctx context.Context, ec *a2asrv.ExecutorContext,
) iter.Seq2[a2a.Event, error] {
	return func(yield func(a2a.Event, error) bool) {
		team, _ := ec.ServiceParams.Get("x-workshop-team")
		version, _ := ec.ServiceParams.Get("A2A-Version")
		ext, _ := a2asrv.ExtensionsFrom(ctx)
		said := []string{
			fmt.Sprintf("User.Name=%q", ec.User.Name),
			fmt.Sprintf("인증됨=%v", ec.User.Authenticated),
			fmt.Sprintf("A2A-Version=%v", version),
			fmt.Sprintf("x-workshop-team=%v", team),
			fmt.Sprintf("확장=%q", ext.RequestedURIs()),
		}
		var parts []*a2a.Part
		for _, s := range said {
			parts = append(parts, a2a.NewTextPart(s))
		}
		reply := a2a.NewMessage(a2a.MessageRoleAgent, parts...)
		reply.ContextID = ec.ContextID
		yield(reply, nil)
	}
}

// endregion

// region: user
// 사용자를 세우는 자리 — 호출 가로채기(CallInterceptor)의 Before.
// 여기서는 머리글을 그대로 믿는다. 이것은 인증이 아니다(누구나
// 머리글을 쓸 수 있다). 토큰을 검사하는 길은 12부.
type userFromHeader struct {
	a2asrv.PassthroughCallInterceptor
}

func (userFromHeader) Before(ctx context.Context,
	cc *a2asrv.CallContext, req *a2asrv.Request,
) (context.Context, any, error) {
	if name, ok := cc.ServiceParams().Get("X-Demo-User"); ok {
		cc.User = a2asrv.NewAuthenticatedUser(name[0], nil)
	}
	return ctx, nil, nil
}

// endregion

func main() {
	port := flag.Int("port", 10905, "들을 포트")
	flag.Parse()
	h := a2asrv.NewHandler(a2asrv.AgentExecutorFunc(who),
		a2asrv.WithCallInterceptors(userFromHeader{}))
	card := steps.EchoCard(fmt.Sprintf("http://127.0.0.1:%d/", *port))
	mux := http.NewServeMux()
	mux.Handle(a2asrv.WellKnownAgentCardPath,
		a2asrv.NewStaticAgentCardHandler(card))
	mux.Handle("/", a2asrv.NewJSONRPCHandler(h))
	addr := fmt.Sprintf("127.0.0.1:%d", *port)
	if err := http.ListenAndServe(addr, mux); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

//@ norun
