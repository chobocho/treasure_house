//go:build !windows

package minipuppy

import (
	"os/exec"
	"syscall"
)

// setProcessGroup 은 자식을 **새 프로세스 그룹의 우두머리**로 만든다.
// 그래야 손자까지 한 번에 신호를 보낼 수 있다.
func setProcessGroup(cmd *exec.Cmd) {
	cmd.SysProcAttr = &syscall.SysProcAttr{Setpgid: true}
}

// killTree 는 프로세스 그룹 전체에 SIGKILL 을 보낸다.
//
// exec.CommandContext 의 기본 동작은 자식 하나만 죽인다. sh -c 가 띄운
// 손자는 살아남아 stdout 파이프를 붙들고, 그래서 cmd.Run() 이 제한 시간이
// 지나도 안 돌아온다. 음수 PID 는 "그 PID 를 우두머리로 하는 그룹 전체"다.
func killTree(cmd *exec.Cmd) error {
	if cmd.Process == nil {
		return nil
	}
	if err := syscall.Kill(-cmd.Process.Pid, syscall.SIGKILL); err == nil {
		return nil
	}
	return cmd.Process.Kill()
}
