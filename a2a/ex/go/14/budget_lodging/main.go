// 완성 숙소 에이전트(agents/lodging)에 예산 확장을 씌워 띄운다.
//
//	go run ./14/budget_lodging --port P [--url U] [--required]
//
// 13부와 같은 수다 — agent.go 는 agents/lodging/main.go 를 가리키는
// 심볼릭 링크라 소문자 card·executor 가 보이고, 아래 init() 이 서버를
// 띄우고 돌아오지 않으므로 그 파일의 main() 은 불리지 않는다.
package main

import (
	"flag"

	"example.com/workshop/14/budget"
	"example.com/workshop/agents/common"
)

// 꾸러미 변수는 init 보다 먼저 정해진다 — ParseArgs 가 함께 읽는다.
var required = flag.Bool("required", false, "확장을 필수로 적는다")

// region: init
func init() {
	args := common.ParseArgs("보물상사 숙소 에이전트(예산 확장)")
	c := card(args.URL)
	budget.Declare(c, *required)
	common.Serve(c, budget.Wrap(executor{}), args.Port,
		common.Options{})
}

// endregion
//@ norun
