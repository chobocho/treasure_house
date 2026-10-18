// 기획 에이전트(agents/planner)를 동료의 포트만 받아 띄운다 — 주소를
// 쉼표로 이은 --agents 가 명세 한 줄(72칸)에 들어가지 않아서.
//
//	go run ./15/planner_at 포트 동료포트…
//
// agent.go 는 agents/planner/main.go 를 가리키는 심볼릭 링크다. 같은
// package main 이 되고, 아래 init() 이 그 파일의 main() 보다 먼저
// 돌아 os.Args 를 --port·--agents 꼴로 바꿔 둔다.
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
