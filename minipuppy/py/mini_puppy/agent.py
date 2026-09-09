"""실행 루프 — 이 파일이 '에이전트'라는 말의 전부다.

    while 남은 걸음이 있다:
        답 = 모델(기록, 도구목록)
        도구를 부르지 않았으면 -> 끝. 그 답이 결과다.
        불렀으면 -> 실행하고 결과를 기록에 붙이고 -> 다시 위로

나머지는 전부 이 루프를 안 죽게 만드는 장치다:
  - 걸음 수 제한: 모델이 같은 도구를 무한히 부르는 사고를 끊는다.
  - 컴팩션: 매 걸음 전에 창이 넘칠지 보고 미리 접는다.
  - 도구 오류를 예외로 던지지 않고 **결과로 돌려준다**: 모델이 오류 문구를
    읽고 스스로 고치게 하려고. 여기서 프로그램을 죽이면 자가 수리가 불가능해진다.
  - 취소 신호: 사용자가 ESC 를 누르면 걸음 사이에서 깨끗하게 멈춘다.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field

from .history import History, Message
from .model import ModelError, ModelReply, ToolCall


@dataclass
class RunResult:
    text: str = ""
    steps: int = 0
    tool_calls: int = 0
    stopped: str = "done"     # done | max_steps | cancelled | model_error
    error: str = ""
    seconds: float = 0.0
    compactions: int = 0


class CancelToken:
    """스레드 사이로 취소를 전한다. ESC 키 감시자가 set() 을 부른다."""

    def __init__(self) -> None:
        self._event = threading.Event()

    def cancel(self) -> None:
        self._event.set()

    def reset(self) -> None:
        self._event.clear()

    @property
    def cancelled(self) -> bool:
        return self._event.is_set()


def to_wire(history: History) -> list:
    """내부 Message 를 모델 API 가 받는 dict 목록으로 옮긴다."""
    out = []
    for m in history.messages:
        if m.role == "tool":
            out.append({"role": "tool", "tool_call_id": m.tool_call_id,
                        "name": m.tool_name, "content": m.content})
        elif m.role == "assistant" and m.tool_name:
            out.append({"role": "assistant", "content": m.content or None,
                        "tool_calls": [{"id": m.tool_call_id, "type": "function",
                                        "function": {"name": m.tool_name,
                                                     "arguments": m.tool_args}}]})
        else:
            out.append({"role": m.role, "content": m.content})
    return out


class Agent:
    def __init__(self, name: str, system_prompt: str, model, registry,
                 tools: list | None = None, bus=None, config=None,
                 display_name: str = "") -> None:
        self.name = name
        self.display_name = display_name or name
        self.system_prompt = system_prompt
        self.model = model
        self.registry = registry
        self.tools = tools              # None 이면 전부 허용
        self.bus = bus
        self.config = config

    # ---- 설정 읽기(없으면 기본값) --------------------------------------
    def _num(self, key: str, fallback):
        if self.config is None:
            return fallback
        raw = self.config.get(key)
        return type(fallback)(raw) if raw is not None else fallback

    def _emit(self, kind: str, text: str, **meta) -> None:
        if self.bus is not None:
            self.bus.emit(kind, text, **meta)

    def new_history(self) -> History:
        return History(self.system_prompt)

    # ---- 본체 ---------------------------------------------------------
    def run(self, prompt: str, history: History | None = None, ctx=None,
            max_steps: int = 20, cancel: CancelToken | None = None,
            depth: int = 0) -> tuple[RunResult, History]:
        history = history if history is not None else self.new_history()
        started = time.time()
        result = RunResult()
        if prompt:
            history.user(prompt)
            self._emit("user", prompt)
        window = self._num("context_window", 16000)
        threshold = self._num("compaction_threshold", 0.75)
        protected = self._num("protected_tokens", 2000)
        max_out = self._num("max_tool_output", 8000)

        for step in range(1, max_steps + 1):
            if cancel is not None and cancel.cancelled:
                result.stopped = "cancelled"
                break
            result.steps = step
            if history.needs_compaction(window, threshold):
                folded = history.compact(protected)
                if folded:
                    result.compactions += 1
                    self._emit("system", "기록 %d건을 접었다 (%d토큰 남음)"
                               % (folded[0], history.total_tokens()))
            schemas = self.registry.schemas(self.tools)
            try:
                reply = self.model.complete(to_wire(history), schemas)
            except ModelError as exc:
                result.stopped, result.error = "model_error", str(exc)
                self._emit("error", "모델 호출 실패: %s" % exc)
                break
            if not isinstance(reply, ModelReply):
                reply = ModelReply(text=str(reply))
            if not reply.wants_tools:
                history.assistant(reply.text)
                result.text = reply.text
                self._emit("agent", reply.text)
                break
            for call in reply.tool_calls:
                self._run_one_tool(call, history, ctx, max_out, result, depth)
        else:
            result.stopped = "max_steps"
            self._emit("warn", "%d걸음을 다 썼다. 여기서 멈춘다." % max_steps)

        result.seconds = round(time.time() - started, 3)
        return result, history

    def _run_one_tool(self, call: ToolCall, history: History, ctx,
                      max_out: int, result: RunResult, depth: int) -> None:
        result.tool_calls += 1
        history.assistant(text="", tool_name=call.name,
                          tool_call_id=call.id, tool_args=call.args)
        self._emit("tool", "%s(%s)" % (call.name, _brief(call.args)),
                   tool=call.name, depth=depth)
        out = self.registry.call(call.name, call.args, ctx=ctx,
                                 allowlist=self.tools, max_output=max_out)
        body = out.content if out.ok else "오류: " + out.content
        history.tool_result(call.id, call.name, body)
        self._emit("tool_out" if out.ok else "warn", body,
                   tool=call.name, truncated=out.truncated)


def _brief(args: dict, limit: int = 60) -> str:
    parts = []
    for k, v in (args or {}).items():
        s = str(v).replace("\n", "⏎")
        if len(s) > limit:
            s = s[:limit] + "…"
        parts.append("%s=%s" % (k, s))
    return ", ".join(parts)
