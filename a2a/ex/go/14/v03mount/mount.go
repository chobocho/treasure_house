// Package v03mount 는 완성 에이전트를 판 0.3 문 하나만 적은 카드로
// 띄운다 — v0.3 만 아는 옛 에이전트의 흉내. 처리기는 v1.0 요청도
// 받는다.
package v03mount

import (
	"context"
	"fmt"
	"net/http"
	"os"

	"github.com/a2aproject/a2a-go/v2/a2a"
	"github.com/a2aproject/a2a-go/v2/a2acompat/a2av0"
	"github.com/a2aproject/a2a-go/v2/a2asrv"
	"github.com/a2aproject/a2a-go/v2/a2asrv/taskstore"
)

// region: mount
func Serve(card *a2a.AgentCard, exec a2asrv.AgentExecutor, port int) {
	old := *card.SupportedInterfaces[0] // 주소는 그대로 두고
	old.ProtocolVersion = a2av0.Version // 판 0.3 문 하나만
	card.SupportedInterfaces = []*a2a.AgentInterface{&old}
	store := taskstore.NewInMemory(&taskstore.InMemoryStoreConfig{
		Authenticator: anyone,
	})
	h := a2asrv.NewHandler(exec,
		a2asrv.WithCapabilityChecks(&card.Capabilities),
		a2asrv.WithTaskStore(store))
	newer := a2asrv.NewJSONRPCHandler(h)
	older := a2av0.NewJSONRPCHandler(h)
	mux := http.NewServeMux()
	// v1.0 과 v0.3 의 칸을 한 JSON 에 섞은 카드
	compat := a2av0.NewStaticAgentCardProducer(card)
	mux.Handle(a2asrv.WellKnownAgentCardPath,
		a2asrv.NewAgentCardHandler(compat))
	// 한 경로에 두 판 — 가르는 일은 우리 몫이다(§3.6.2: 빈 값은 0.3)
	mux.HandleFunc("/{$}", func(w http.ResponseWriter,
		r *http.Request) {
		v := r.Header.Get("A2A-Version")
		if v == "" || v == string(a2av0.Version) {
			older.ServeHTTP(w, r)
			return
		}
		newer.ServeHTTP(w, r)
	})
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
