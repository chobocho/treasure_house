// Package restmount 는 완성 에이전트의 카드와 실행기를 HTTP+JSON(REST)
// 문 하나로 띄운다. agents/common.Serve 의 REST 판이다.
package restmount

import (
	"context"
	"fmt"
	"net/http"
	"os"

	"github.com/a2aproject/a2a-go/v2/a2a"
	"github.com/a2aproject/a2a-go/v2/a2asrv"
	"github.com/a2aproject/a2a-go/v2/a2asrv/taskstore"
)

// region: mount
func Serve(card *a2a.AgentCard, exec a2asrv.AgentExecutor, port int) {
	// 카드의 문 하나를 HTTP+JSON 으로 바꿔 적는다(주소는 그대로).
	card.SupportedInterfaces[0].ProtocolBinding =
		a2a.TransportProtocolHTTPJSON
	store := taskstore.NewInMemory(&taskstore.InMemoryStoreConfig{
		Authenticator: anyone,
	})
	h := a2asrv.NewHandler(exec,
		a2asrv.WithCapabilityChecks(&card.Capabilities),
		a2asrv.WithTaskStore(store))
	mux := http.NewServeMux()
	mux.Handle(a2asrv.WellKnownAgentCardPath,
		a2asrv.NewStaticAgentCardHandler(card))
	// JSON-RPC 의 NewJSONRPCHandler 자리에 NewRESTHandler
	mux.Handle("/", a2asrv.NewRESTHandler(h))
	addr := fmt.Sprintf("127.0.0.1:%d", port)
	if err := http.ListenAndServe(addr, mux); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

// endregion

// anyone: 익명도 한 사람으로 본다(agents/common 의 owner 와 같은 뜻).
func anyone(ctx context.Context) (string, error) {
	return "anonymous", nil
}
