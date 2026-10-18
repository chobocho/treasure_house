// Package grpcmount 는 완성 에이전트의 카드와 실행기를 gRPC 문 하나로
// 띄운다. 카드는 여전히 HTTP 로 내준다. agents/common.Serve 의 gRPC 판.
//
// --grpc-port·--grpc-url 은 이 패키지가 등록한다 — 패키지 변수는
// main 패키지의 init() 보다 먼저 만들어지므로 ParseArgs 가 함께 읽는다.
package grpcmount

import (
	"context"
	"flag"
	"fmt"
	"net"
	"net/http"
	"os"

	"github.com/a2aproject/a2a-go/v2/a2a"
	a2agrpc "github.com/a2aproject/a2a-go/v2/a2agrpc/v1"
	"github.com/a2aproject/a2a-go/v2/a2asrv"
	"github.com/a2aproject/a2a-go/v2/a2asrv/taskstore"
	"google.golang.org/grpc"
)

var (
	grpcPort = flag.Int("grpc-port", 0, "gRPC 로 붙을 포트(필수)")
	grpcURL  = flag.String("grpc-url", "", "카드에 적을 gRPC 주소")
)

// region: mount
func Serve(card *a2a.AgentCard, exec a2asrv.AgentExecutor, port int) {
	target := fmt.Sprintf("127.0.0.1:%d", *grpcPort)
	if *grpcURL == "" {
		*grpcURL = target
	}
	// 카드의 문 하나를 GRPC 로 — 주소는 "호스트:포트"(스킴 없음)
	card.SupportedInterfaces[0] =
		a2a.NewAgentInterface(*grpcURL, a2a.TransportProtocolGRPC)
	store := taskstore.NewInMemory(&taskstore.InMemoryStoreConfig{
		Authenticator: anyone,
	})
	h := a2asrv.NewHandler(exec,
		a2asrv.WithCapabilityChecks(&card.Capabilities),
		a2asrv.WithTaskStore(store))
	server := grpc.NewServer()
	a2agrpc.NewHandler(h).RegisterWith(server)
	lis, err := net.Listen("tcp", target)
	exitIf(err)
	go func() { exitIf(server.Serve(lis)) }()
	// 발견은 바인딩과 따로 — 카드는 HTTP 의 잘 알려진 경로에
	mux := http.NewServeMux()
	mux.Handle(a2asrv.WellKnownAgentCardPath,
		a2asrv.NewStaticAgentCardHandler(card))
	addr := fmt.Sprintf("127.0.0.1:%d", port)
	exitIf(http.ListenAndServe(addr, mux))
}

// endregion

func exitIf(err error) {
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

// anyone: 익명도 한 사람으로 본다(agents/common 의 owner 와 같은 뜻).
func anyone(ctx context.Context) (string, error) {
	return "anonymous", nil
}
