// 완성 숙소 에이전트(agents/lodging)를 HTTP+JSON 문으로 띄운다.
//
//	go run ./13/rest_lodging --port P [--url U]
//
// agent.go 는 agents/lodging/main.go 를 가리키는 심볼릭 링크다 — 같은
// package main 이 되어 소문자 card·executor 가 보인다. 그 파일의
// main() 은 불리지 않는다: 아래 init() 이 서버를 띄우고 돌아오지
// 않기 때문이다(init 은 main 보다 먼저 돈다).
package main

import (
	"example.com/workshop/13/restmount"
	"example.com/workshop/agents/common"
)

// region: init
func init() {
	args := common.ParseArgs("보물상사 숙소 에이전트(HTTP+JSON)")
	restmount.Serve(card(args.URL), executor{}, args.Port)
}

// endregion
//@ norun
