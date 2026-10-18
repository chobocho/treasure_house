// 완성 식사 에이전트(agents/catering)를 HTTP+JSON 문으로 띄운다.
//
//	go run ./13/rest_catering --port P [--step-ms N]
//
// agent.go 는 agents/catering/main.go 를 가리키는 심볼릭 링크다.
// 짜임은 13/rest_lodging 과 같다 — init() 이 띄우고 돌아오지 않는다.
package main

import (
	"flag"

	"example.com/workshop/13/restmount"
	"example.com/workshop/agents/common"
)

// region: init
func init() {
	step := flag.Int("step-ms", 100, "끼니 사이 쉬는 시간(ms)")
	args := common.ParseArgs("보물상사 식사 에이전트(HTTP+JSON)")
	restmount.Serve(card(args.URL), executor{*step}, args.Port)
}

// endregion

//@ norun
