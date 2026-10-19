// 16/intstest 의 시험을 09/run_tests 로 돌린다 — 명세가 16부의
// 예제를 부르게 해서 시험 파일이 캡처의 입력(ex/go/16)에 들게 한다.
//
//	go run ./16/run_tests
package main

import (
	"os"
	"os/exec"
)

func main() {
	cmd := exec.Command("go", "run", "./09/run_tests", "./16/intstest")
	cmd.Stdout, cmd.Stderr = os.Stdout, os.Stderr
	if cmd.Run() != nil {
		os.Exit(1)
	}
}

//@ norun
