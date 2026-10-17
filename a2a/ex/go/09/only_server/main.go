// 9장의 실험 서버 — Go SDK 에서 두드러지는 손잡이를 경로마다 하나씩.
//
//	go run ./09/only_server --port P --down URL
//
//	/audit   호출 가로채기 둘(앞뒤 차례)과 일찍 답하기(핑 → 퐁)
//	/panic   panic 하는 실행기 — 처리기 옵션 없이
//	/panic2  같은 실행기 + WithExecutionPanicHandler
//	/relay   a2aext 로 확장 머리글·metadata 를 아래(--down)로 넘긴다
//	/who     받은 확장과 metadata 를 돌려주는 아래 에이전트
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

// region: audit
// audit 는 앞뒤에 이름을 찍는 가로채기다. 둘을 달면 Before 는 단
// 차례로, After 는 거꾸로 돈다.
type audit struct{ name string }

func (a audit) Before(ctx context.Context, cc *a2asrv.CallContext,
	req *a2asrv.Request) (context.Context, any, error) {
	fmt.Printf("[%s] Before %s\n", a.name, cc.Method())
	return ctx, nil, nil
}

func (a audit) After(ctx context.Context, cc *a2asrv.CallContext,
	resp *a2asrv.Response) error {
	fmt.Printf("[%s] After  %s → %T err=%v\n", a.name, cc.Method(),
		resp.Payload, resp.Err)
	return nil
}

// endregion

// region: ping
// ping 은 "핑" 이면 처리기를 부르지 않고 곧바로 답한다 — Before 가
// 결과를 돌려주면 실행기는 돌지 않는다.
type ping struct {
	a2asrv.PassthroughCallInterceptor
}

func (ping) Before(ctx context.Context, cc *a2asrv.CallContext,
	req *a2asrv.Request) (context.Context, any, error) {
	r, ok := req.Payload.(*a2a.SendMessageRequest)
	if !ok || len(r.Message.Parts) == 0 ||
		r.Message.Parts[0].Text() != "핑" {
		return ctx, nil, nil
	}
	pong := a2a.NewMessage(a2a.MessageRoleAgent, a2a.NewTextPart("퐁"))
	return ctx, a2a.SendMessageResult(pong), nil
}

// endregion

// region: panic
// boom 은 첫 이벤트도 내기 전에 panic 하는 실행기다.
func boom(ctx context.Context, ec *a2asrv.ExecutorContext,
) iter.Seq2[a2a.Event, error] {
	return func(yield func(a2a.Event, error) bool) {
		panic("숙소 목록이 비었다")
	}
}

// 우리 처리기 — 까닭만 남기고 오류 코드를 정한다(스택은 버린다).
func onPanic(r any) error {
	fmt.Println("[panic2] 처리기가 받은 것:", r)
	return fmt.Errorf("%w: 실행기가 멈췄습니다", a2a.ErrInternalError)
}

// endregion

func main() {
	port := flag.Int("port", 10970, "들을 포트")
	down := flag.String("down", "", "relay 가 부를 아래 에이전트 주소")
	flag.Parse()
	mux := http.NewServeMux()
	rpc := func(path string, h a2asrv.RequestHandler) {
		mux.Handle("POST "+path, a2asrv.NewJSONRPCHandler(h))
	}
	// region: mount
	rpc("/audit", a2asrv.NewHandler(steps.Echo{},
		a2asrv.WithCallInterceptors(audit{"바깥"}, audit{"안쪽"},
			ping{})))
	rpc("/panic", a2asrv.NewHandler(a2asrv.AgentExecutorFunc(boom)))
	rpc("/panic2", a2asrv.NewHandler(a2asrv.AgentExecutorFunc(boom),
		a2asrv.WithExecutionPanicHandler(onPanic)))
	rpc("/relay", a2asrv.NewHandler(relay{*down},
		a2asrv.WithCallInterceptors(serverPropagator())))
	rpc("/who", a2asrv.NewHandler(a2asrv.AgentExecutorFunc(who)))
	// endregion
	addr := fmt.Sprintf("127.0.0.1:%d", *port)
	if err := http.ListenAndServe(addr, mux); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

//@ norun
