// 고치기 전의 기획 에이전트(agent.go)를 동료의 포트만 받아 띄운다 —
// 15/planner_at 과 같은 겉층이고, agent.go 만 링크가 아닌 옛 사본이다.
//
//	go run ./15/old_at 포트 동료포트…
package main

import (
	"fmt"
	"os"
	"strings"
)

func init() {
	var urls []string
	for _, p := range os.Args[2:] {
		urls = append(urls, fmt.Sprintf("http://127.0.0.1:%s/", p))
	}
	os.Args = []string{os.Args[0], "--port", os.Args[1],
		"--agents", strings.Join(urls, ",")}
}

//@ norun
