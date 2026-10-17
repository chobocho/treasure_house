// 2단계 — 견적 에이전트 서버: JSON-RPC 를 --path 에, POST 로만 단다.
//
//	go run ./09/step2_task --port P [--url U] [--path /a2a]
package main

import (
	"flag"
	"fmt"
	"net/http"
	"os"

	"github.com/a2aproject/a2a-go/v2/a2asrv"

	"example.com/workshop/09/steps"
)

// region: serve
func main() {
	port := flag.Int("port", 10902, "들을 포트")
	path := flag.String("path", "/", "JSON-RPC 를 달 경로")
	url := flag.String("url", "", "카드에 적을 바깥 주소")
	flag.Parse()
	if *url == "" {
		*url = fmt.Sprintf("http://127.0.0.1:%d%s", *port, *path)
	}
	card := steps.QuoteCard(*url)
	handler := a2asrv.NewHandler(steps.Quote{},
		a2asrv.WithCapabilityChecks(&card.Capabilities))

	mux := http.NewServeMux()
	mux.Handle("GET "+a2asrv.WellKnownAgentCardPath,
		a2asrv.NewStaticAgentCardHandler(card))
	// 패턴에 방법(POST)과 경로를 함께 — 나머지는 ServeMux 가 거절
	mux.Handle("POST "+*path, a2asrv.NewJSONRPCHandler(handler))

	addr := fmt.Sprintf("127.0.0.1:%d", *port)
	if err := http.ListenAndServe(addr, mux); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

// endregion

//@ norun
