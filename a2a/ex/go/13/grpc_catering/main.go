// 완성 식사 에이전트(agents/catering)를 gRPC 문으로 띄운다.
//
//	go run ./13/grpc_catering --port P --grpc-port G [--step-ms N]
//
// agent.go 는 agents/catering/main.go 를 가리키는 심볼릭 링크다.
// 짜임은 13/rest_catering 과 같다 — init() 이 띄우고 돌아오지 않는다.
package main

import (
	"flag"

	"example.com/workshop/13/grpcmount"
	"example.com/workshop/agents/common"
)

// region: init
func init() {
	step := flag.Int("step-ms", 100, "끼니 사이 쉬는 시간(ms)")
	args := common.ParseArgs("보물상사 식사 에이전트(gRPC)")
	grpcmount.Serve(card(args.URL), executor{*step}, args.Port)
}

// endregion

//@ norun
