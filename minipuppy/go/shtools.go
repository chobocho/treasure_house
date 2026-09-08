package minipuppy

import (
	"bytes"
	"context"
	"fmt"
	"os/exec"
	"runtime"
	"strconv"
	"strings"
	"time"
)

// denyList 는 물어보지도 않고 막는 것들.
var denyList = []string{
	"rm -rf /", "mkfs", ":(){:|:&};:", "dd if=", "shutdown", "reboot",
	"format c:", "del /f /s /q c:\\",
}

// LooksDangerous 는 걸린 패턴을 준다. 안 걸리면 빈 문자열.
func LooksDangerous(command string) string {
	low := strings.Join(strings.Fields(strings.ToLower(command)), " ")
	for _, p := range denyList {
		if strings.Contains(low, p) {
			return p
		}
	}
	return ""
}

// ShellResult 는 명령 하나의 결과.
type ShellResult struct {
	Code     int
	Stdout   string
	Stderr   string
	Seconds  float64
	TimedOut bool
}

// RunShell 은 명령 하나를 돌린다.
//
// 여기서 Go 가 파이썬보다 까다롭다. exec.CommandContext 는 시간이 지나면
// **자식 하나만** 죽인다. 그런데 우리가 띄우는 자식은 sh(또는 cmd)이고,
// 진짜 오래 도는 것은 그 손자다. 손자가 살아 stdout 파이프를 붙들고 있으면
// cmd.Run() 은 제한 시간이 지나도 돌아오지 않는다 — 시간 제한이 있는 척만 한다.
//
// 그래서 두 가지를 더 건다:
//   - Cancel: 프로세스 **나무 전체**를 죽인다(proc_unix.go / proc_windows.go)
//   - WaitDelay: 그러고도 파이프가 안 닫히면 그만 기다리고 돌아온다
//
// 이 두 줄이 없으면 "sleep 30 을 2초 제한으로 돌렸는데 29초 걸린다".
func RunShell(ctx context.Context, command, cwd string, timeout time.Duration) (ShellResult, error) {
	if hit := LooksDangerous(command); hit != "" {
		return ShellResult{}, fmt.Errorf("막힌 명령이다(%s). 사람이 직접 실행해라.", hit)
	}
	if timeout <= 0 {
		timeout = 30 * time.Second
	}
	runCtx, cancel := context.WithTimeout(ctx, timeout)
	defer cancel()

	var cmd *exec.Cmd
	if runtime.GOOS == "windows" {
		cmd = exec.CommandContext(runCtx, "cmd", "/C", command)
	} else {
		cmd = exec.CommandContext(runCtx, "sh", "-c", command)
	}
	cmd.Dir = cwd
	setProcessGroup(cmd)
	cmd.Cancel = func() error { return killTree(cmd) }
	cmd.WaitDelay = 2 * time.Second
	var out, errBuf bytes.Buffer
	cmd.Stdout, cmd.Stderr = &out, &errBuf

	started := time.Now()
	err := cmd.Run()
	elapsed := time.Since(started).Seconds()

	res := ShellResult{
		Stdout: out.String(), Stderr: errBuf.String(),
		Seconds: float64(int(elapsed*1000)) / 1000,
		Code:    cmd.ProcessState.ExitCode(),
	}
	if runCtx.Err() == context.DeadlineExceeded {
		res.TimedOut = true
	}
	_ = err // 종료 코드는 ProcessState 에서 읽는다. 0 이 아닌 것은 오류가 아니다.
	return res, nil
}

type runArgs struct {
	Command string `json:"command" desc:"실행할 명령줄" required:"true"`
	Timeout int    `json:"timeout" desc:"제한 시간(초). 0 이면 설정값"`
}

// RegisterShellTools 는 run_command 를 등록한다.
func RegisterShellTools(r *Registry, defaultTimeout time.Duration) {
	Register(r, "run_command", "셸 명령 하나를 작업 뿌리에서 실행한다.",
		func(w *Workspace, a runArgs) (string, error) {
			limit := defaultTimeout
			if a.Timeout > 0 {
				limit = time.Duration(a.Timeout) * time.Second
			}
			res, err := RunShell(context.Background(), a.Command, w.Root, limit)
			if err != nil {
				return "", err
			}
			head := fmt.Sprintf("$ %s\n(종료코드 %s, %.2f초)",
				a.Command, strconv.Itoa(res.Code), res.Seconds)
			if res.TimedOut {
				head += fmt.Sprintf(" ⏱ 제한 시간 %s를 넘겨 죽였다", limit)
			}
			var body []string
			if strings.TrimSpace(res.Stdout) != "" {
				body = append(body, strings.TrimRight(res.Stdout, "\r\n"))
			}
			if strings.TrimSpace(res.Stderr) != "" {
				body = append(body, "[stderr]\n"+strings.TrimRight(res.Stderr, "\r\n"))
			}
			if len(body) == 0 {
				return head + "\n(출력 없음)", nil
			}
			return head + "\n" + strings.Join(body, "\n"), nil
		})
}
