"""셸 도구 — 에이전트가 명령을 돌려 결과를 보는 층.

코딩 에이전트에서 가장 위험한 도구다. 세 가지를 지킨다.
  1. **시간 제한**. 대화형 명령(vim, git rebase -i)에 걸리면 영원히 멈춘다.
     제한 시간이 지나면 프로세스 나무를 통째로 죽인다.
  2. **작업 디렉터리 고정**. cd 로 뿌리를 벗어나도 다음 호출은 다시 뿌리에서
     시작한다. 셸 상태는 호출 사이에 이어지지 않는다 — 이어지면 재현이 안 된다.
  3. **출력 상한**. 로그 40만 줄이 그대로 컨텍스트에 들어오면 창이 죽는다.
     앞뒤만 남기고 가운데를 자른다(tools.py 의 max_output 이 처리).

Windows 와 POSIX 에서 프로세스를 죽이는 방법이 다르다 — POSIX 는 프로세스
그룹에 SIGKILL, Windows 는 taskkill /T. 둘 다 처리한다.
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time

from .tools import ToolError

# 물어보지도 않고 막는 것들. "확인 후 실행"으로 넘길 수준이 아니다.
DENY = (
    "rm -rf /", "mkfs", ":(){:|:&};:", "dd if=", "shutdown", "reboot",
    "format c:", "del /f /s /q c:\\",
)


def looks_dangerous(command: str) -> str:
    low = " ".join(command.lower().split())
    for pat in DENY:
        if pat in low:
            return pat
    return ""


def _kill_tree(proc: subprocess.Popen) -> None:
    if proc.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                       capture_output=True)
    else:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            proc.kill()


def run_shell(command: str, cwd: str, timeout: int = 30) -> dict:
    """명령 하나를 돌리고 {code, stdout, stderr, seconds, timed_out} 를 준다."""
    hit = looks_dangerous(command)
    if hit:
        raise ToolError("막힌 명령이다(%s). 사람이 직접 실행해라." % hit)
    kwargs = {}
    if os.name == "nt":
        kwargs["creationflags"] = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    else:
        kwargs["start_new_session"] = True
    started = time.time()
    proc = subprocess.Popen(
        command, shell=True, cwd=cwd, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace",
        **kwargs)
    timed_out = False
    try:
        out, err = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        _kill_tree(proc)
        try:
            out, err = proc.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            out, err = "", ""
    return {
        "code": proc.returncode, "stdout": out or "", "stderr": err or "",
        "seconds": round(time.time() - started, 3), "timed_out": timed_out,
    }


def register(reg, default_timeout: int = 30):
    @reg.register
    def run_command(ctx, command: str, timeout: int = 0) -> str:
        """셸 명령 하나를 작업 뿌리에서 실행한다.

        Args:
          command: 실행할 명령줄
          timeout: 제한 시간(초). 0 이면 설정값을 쓴다
        """
        limit = timeout if timeout > 0 else default_timeout
        res = run_shell(command, cwd=str(ctx.root), timeout=limit)
        head = "$ %s\n(종료코드 %s, %.2f초)" % (command, res["code"], res["seconds"])
        if res["timed_out"]:
            head += " ⏱ 제한 시간 %d초를 넘겨 죽였다" % limit
        body = []
        if res["stdout"].strip():
            body.append(res["stdout"].rstrip())
        if res["stderr"].strip():
            body.append("[stderr]\n" + res["stderr"].rstrip())
        return head + ("\n" + "\n".join(body) if body else "\n(출력 없음)")

    return reg


def python_exe() -> str:
    return sys.executable or "python"
