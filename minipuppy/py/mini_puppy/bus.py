"""메시지 버스 — 에이전트 코드가 터미널을 직접 만지지 못하게 막는 층.

왜 CLI에 버스가 필요한가:
  - 에이전트 실행은 async, 화면 갱신은 다른 박자로 돈다.
  - 도구가 print() 를 쓰면 스트리밍 중인 답변 위에 글자가 덮어써진다.
  - 같은 사건을 화면·로그·테스트 세 곳이 다른 방식으로 받아야 한다.

그래서 모든 출력은 Message 로 만들어 버스에 넣고, 렌더러가 꺼내 그린다.
테스트는 CollectingSink 를 붙여 화면 없이 사건만 검사한다.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Callable, Iterable

# 사건 종류. 렌더러는 이 값으로 색과 모양을 고른다.
KINDS = (
    "user",       # 사람이 친 것
    "agent",      # 모델이 낸 글
    "tool",       # 도구 호출 시작
    "tool_out",   # 도구 결과
    "info",       # 안내
    "warn",       # 경고
    "error",      # 오류
    "system",     # 컴팩션 등 내부 사건
)


@dataclass(frozen=True)
class Message:
    kind: str
    text: str
    meta: dict = field(default_factory=dict)
    ts: float = field(default_factory=time.time)

    def __post_init__(self) -> None:
        if self.kind not in KINDS:
            raise ValueError(f"모르는 사건 종류: {self.kind!r}")


Sink = Callable[[Message], None]


class MessageBus:
    """여러 스레드가 넣고, 붙은 싱크들이 순서대로 받는다.

    락 하나로 순서를 지킨다. 싱크가 예외를 던져도 다른 싱크는 계속 받는다
    — 렌더러 하나가 죽었다고 에이전트를 멈추면 안 되기 때문.
    """

    def __init__(self) -> None:
        self._sinks: list[Sink] = []
        self._lock = threading.RLock()
        self._log: list[Message] = []
        self._sink_errors: list[BaseException] = []

    def subscribe(self, sink: Sink) -> Sink:
        with self._lock:
            self._sinks.append(sink)
        return sink

    def unsubscribe(self, sink: Sink) -> None:
        with self._lock:
            if sink in self._sinks:
                self._sinks.remove(sink)

    def emit(self, kind: str, text: str, **meta) -> Message:
        msg = Message(kind=kind, text=text, meta=meta)
        with self._lock:
            self._log.append(msg)
            sinks = list(self._sinks)
        for sink in sinks:
            try:
                sink(msg)
            except BaseException as exc:  # 싱크 하나의 사고가 번지지 않게
                self._sink_errors.append(exc)
        return msg

    # 편의 어댑터 — 호출부가 kind 문자열을 외우지 않아도 되게
    def info(self, text: str, **m) -> Message:
        return self.emit("info", text, **m)

    def warn(self, text: str, **m) -> Message:
        return self.emit("warn", text, **m)

    def error(self, text: str, **m) -> Message:
        return self.emit("error", text, **m)

    @property
    def log(self) -> list[Message]:
        with self._lock:
            return list(self._log)

    @property
    def sink_errors(self) -> list[BaseException]:
        return list(self._sink_errors)

    def texts(self, kind: str | None = None) -> list[str]:
        return [m.text for m in self.log if kind is None or m.kind == kind]


class CollectingSink:
    """테스트용 싱크. 받은 것을 그대로 쌓아 둔다."""

    def __init__(self, kinds: Iterable[str] | None = None) -> None:
        self.kinds = set(kinds) if kinds else None
        self.messages: list[Message] = []

    def __call__(self, msg: Message) -> None:
        if self.kinds is None or msg.kind in self.kinds:
            self.messages.append(msg)

    def __len__(self) -> int:
        return len(self.messages)


ICONS = {
    "user": "▶",
    "agent": "🐶",
    "tool": "⚙",
    "tool_out": "  ",
    "info": "ℹ",
    "warn": "⚠",
    "error": "✖",
    "system": "·",
}


def console_sink(msg: Message) -> None:
    """가장 단순한 렌더러. 실제 Code Puppy 는 여기에 rich 를 쓴다.

    여러 줄짜리 도구 결과는 이어지는 줄도 같은 자리에서 시작하게 들여쓴다 —
    안 그러면 행 번호가 들쭉날쭉해 보인다.
    """
    icon = ICONS.get(msg.kind, " ")
    head, *rest = msg.text.split(chr(10))
    pad = " " * (len(icon) + 1)
    print(icon + " " + head)
    for line in rest:
        print(pad + line)
