// 완성 숙소 에이전트(agents/lodging)를 판 0.3 문 하나만 적은 카드로
// 띄운다 — v0.3 만 아는 옛 에이전트의 흉내.
//
//	go run ./14/old_lodging --port P [--url U]
//
// agent.go 는 agents/lodging/main.go 를 가리키는 심볼릭 링크다(13부와
// 같은 수 — init() 이 서버를 띄우고 돌아오지 않는다).
package main

import (
	"example.com/workshop/14/v03mount"
	"example.com/workshop/agents/common"
)

// region: init
func init() {
	args := common.ParseArgs("보물상사 숙소 에이전트(v0.3)")
	v03mount.Serve(card(args.URL), executor{}, args.Port)
}

// endregion
//@ norun
