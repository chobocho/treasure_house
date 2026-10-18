// 완성 숙소 에이전트(agents/lodging)를 gRPC 문으로 띄운다.
//
//	go run ./13/grpc_lodging --port P --grpc-port G [--grpc-url U]
//
// agent.go 는 agents/lodging/main.go 를 가리키는 심볼릭 링크다.
// 짜임은 13/rest_lodging 과 같다 — init() 이 띄우고 돌아오지 않는다.
package main

import (
	"example.com/workshop/13/grpcmount"
	"example.com/workshop/agents/common"
)

// region: init
func init() {
	args := common.ParseArgs("보물상사 숙소 에이전트(gRPC)")
	grpcmount.Serve(card(args.URL), executor{}, args.Port)
}

// endregion
//@ norun
