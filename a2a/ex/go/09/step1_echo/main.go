// 1단계 — 메아리 에이전트 서버: 카드와 JSON-RPC 를 net/http 에 단다.
//
//	go run ./09/step1_echo --port P [--url 카드에_적을_주소]
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
	port := flag.Int("port", 10901, "들을 포트")
	url := flag.String("url", "", "카드에 적을 바깥 주소")
	flag.Parse()
	if *url == "" {
		*url = fmt.Sprintf("http://127.0.0.1:%d/", *port)
	}
	card := steps.EchoCard(*url)
	handler := a2asrv.NewHandler(steps.Echo{},
		a2asrv.WithCapabilityChecks(&card.Capabilities))

	mux := http.NewServeMux() // 길은 우리가 정한다
	mux.Handle(a2asrv.WellKnownAgentCardPath,
		a2asrv.NewStaticAgentCardHandler(card))
	mux.Handle("/", a2asrv.NewJSONRPCHandler(handler))

	addr := fmt.Sprintf("127.0.0.1:%d", *port)
	if err := http.ListenAndServe(addr, mux); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

// endregion

//@ norun
