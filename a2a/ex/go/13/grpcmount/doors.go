package grpcmount

// 한 서버, 세 바인딩 — JSON-RPC(/)·HTTP+JSON(/rest)·gRPC(--grpc-port)
// 세 문을 한꺼번에 연다. 요청 처리기와 작업 저장소는 하나다.
// 어느 문으로 들어왔는지 한 줄씩 찍는다(카드 요청은 [카드]).

import (
	"context"
	"fmt"
	"net"
	"net/http"
	"strings"

	"github.com/a2aproject/a2a-go/v2/a2a"
	a2agrpc "github.com/a2aproject/a2a-go/v2/a2agrpc/v1"
	"github.com/a2aproject/a2a-go/v2/a2asrv"
	"github.com/a2aproject/a2a-go/v2/a2asrv/taskstore"
	"google.golang.org/grpc"
)

func door(path string) string {
	switch {
	case strings.HasPrefix(path, "/.well-known/"):
		return "카드"
	case strings.HasPrefix(path, "/rest/"):
		return "HTTP+JSON"
	}
	return "JSONRPC"
}

func logHTTP(h http.Handler) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		path := r.URL.Path
		fmt.Printf("[%s] %s %s\n", door(path), r.Method, path)
		h.ServeHTTP(w, r)
	}
}

func logUnary(ctx context.Context, req any,
	info *grpc.UnaryServerInfo, next grpc.UnaryHandler) (any, error) {
	fmt.Printf("[GRPC] %s\n", info.FullMethod)
	return next(ctx, req)
}

func logStream(srv any, ss grpc.ServerStream,
	info *grpc.StreamServerInfo, next grpc.StreamHandler) error {
	fmt.Printf("[GRPC] %s\n", info.FullMethod)
	return next(srv, ss)
}

// region: doors
func ServeDoors(card *a2a.AgentCard, exec a2asrv.AgentExecutor,
	port int) {
	httpURL := card.SupportedInterfaces[0].URL
	target := fmt.Sprintf("127.0.0.1:%d", *grpcPort)
	if *grpcURL == "" {
		*grpcURL = target
	}
	// 카드에 세 문을 모두 적는다(§5.2 MUST) — 차례가 서버의 선호다
	card.SupportedInterfaces = append(card.SupportedInterfaces,
		a2a.NewAgentInterface(httpURL+"rest",
			a2a.TransportProtocolHTTPJSON),
		a2a.NewAgentInterface(*grpcURL, a2a.TransportProtocolGRPC))
	store := taskstore.NewInMemory(&taskstore.InMemoryStoreConfig{
		Authenticator: anyone,
	})
	h := a2asrv.NewHandler(exec,
		a2asrv.WithCapabilityChecks(&card.Capabilities),
		a2asrv.WithTaskStore(store))
	server := grpc.NewServer(grpc.UnaryInterceptor(logUnary),
		grpc.StreamInterceptor(logStream))
	a2agrpc.NewHandler(h).RegisterWith(server)
	lis, err := net.Listen("tcp", target)
	exitIf(err)
	go func() { exitIf(server.Serve(lis)) }()
	mux := http.NewServeMux()
	mux.Handle(a2asrv.WellKnownAgentCardPath,
		a2asrv.NewStaticAgentCardHandler(card))
	mux.Handle("/rest/",
		http.StripPrefix("/rest", a2asrv.NewRESTHandler(h)))
	mux.Handle("/", a2asrv.NewJSONRPCHandler(h))
	addr := fmt.Sprintf("127.0.0.1:%d", port)
	exitIf(http.ListenAndServe(addr, logHTTP(mux)))
}

// endregion
