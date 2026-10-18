// 역할을 못 찾았을 때 Go 기획 에이전트(agents/planner)가 무엇을 하는지
// 떼어 본다 — discover 가 돌려준 맵에 없는 역할을 꺼내면 nil 이 나오고,
// 그 nil 카드가 getToken·delegate 로 들어간다.
//
// agent.go 는 agents/planner/main.go 의 심볼릭 링크다. init() 이 그
// 파일의 main() 보다 먼저 돌고, 끝나면 os.Exit 로 나간다.
package main

import (
	"context"
	"fmt"
	"os"

	"github.com/a2aproject/a2a-go/v2/a2a"
)

// region: nil
func init() {
	cards := map[string]*a2a.AgentCard{} // 아무 역할도 못 찾은 결과
	fmt.Println(`cards["settle"] =`, cards["settle"])
	e := &executor{clientID: "planner", secret: "planner-secret"}
	try("getToken", func() {
		e.getToken(cards["settle"], "payment:read")
	})
	try("delegate", func() {
		ctx := context.Background()
		_, err := delegate(ctx, cards["lodging"], nil, "c1", "")
		fmt.Println("delegate 오류:", err)
	})
	os.Exit(0)
}

// try 는 f 를 부르고, 패닉이 나면 그 값을 찍고 넘어간다.
func try(name string, f func()) {
	defer func() {
		if r := recover(); r != nil {
			fmt.Println(name, "패닉:", r)
		}
	}()
	f()
}

// endregion
