// 기획 에이전트(agents/planner)를 탭 뒤에 띄운다 — 15/planner_at 에
// 카드에 적을 바깥 주소(탭의 포트)를 하나 더 받는다.
//
//	go run ./15/planner_via 포트 탭포트 동료포트…
//
// agent.go 는 agents/planner/main.go 를 가리키는 심볼릭 링크다.
package main

import (
	"fmt"
	"os"
	"strings"
)

func init() {
	var urls []string
	for _, p := range os.Args[3:] {
		urls = append(urls, fmt.Sprintf("http://127.0.0.1:%s/", p))
	}
	os.Args = []string{os.Args[0], "--port", os.Args[1],
		"--url", fmt.Sprintf("http://127.0.0.1:%s/", os.Args[2]),
		"--agents", strings.Join(urls, ",")}
}

//@ norun
