//go:build windows

package minipuppy

import "os/exec"

// setProcessGroup — Windows 에는 POSIX 프로세스 그룹이 없다. 대신 종료할 때
// taskkill /T 로 나무를 통째로 밟는다(아래 killTree).
func setProcessGroup(_ *exec.Cmd) {}

// killTree 는 자식과 그 자식들까지 죽인다.
//
// exec.CommandContext 의 기본 동작은 **자식 하나만** 죽인다. cmd /C 가 띄운
// 손자(ping, python …)는 살아남아 stdout 파이프를 붙들고, 그래서 cmd.Run()
// 이 제한 시간이 지나도 안 돌아온다. 이 함수와 WaitDelay 가 그 구멍을 막는다.
func killTree(cmd *exec.Cmd) error {
	if cmd.Process == nil {
		return nil
	}
	pid := cmd.Process.Pid
	_ = exec.Command("taskkill", "/F", "/T", "/PID", itoaPID(pid)).Run()
	return cmd.Process.Kill()
}
