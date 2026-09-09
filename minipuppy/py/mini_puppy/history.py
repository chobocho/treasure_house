"""대화 기록과 컴팩션 — 창이 터지기 전에 스스로 줄이는 층.

코딩 에이전트가 다른 챗봇과 갈리는 지점이 여기다. 도구 결과 하나가
파일 전문 2천 줄일 수 있고, 스무 턴이면 어떤 창도 넘친다. 그래서
**언제·무엇을 버릴지**가 설계 결정이 된다.

mini-puppy 의 규칙(Code Puppy 의 _compaction.py 와 같은 골격):
  1. 시스템 프롬프트는 절대 안 지운다 — 지우면 인격이 사라진다.
  2. 최근 protected_tokens 만큼은 절대 안 지운다 — 방금 한 말을 잊으면 안 된다.
  3. 그 사이 구간만 요약 한 덩어리로 바꾼다.
  4. **도구 호출과 그 결과는 절대 갈라놓지 않는다** — 결과만 남으면
     대부분의 모델 API 가 400 을 던진다. 이게 컴팩션의 진짜 함정이다.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable, Iterable

ROLES = ("system", "user", "assistant", "tool")

_CJK = re.compile(
    r"[\u1100-\u11FF\u3040-\u30FF\u3130-\u318F\u3400-\u4DBF"
    r"\u4E00-\u9FFF\uAC00-\uD7AF\uF900-\uFAFF]"
)


def estimate_tokens(text: str) -> int:
    """토크나이저 없이 어림잡는다.

    영어는 대략 4글자에 1토큰, 한글·한자는 대략 1.5글자에 1토큰이다.
    (BPE 가 한글을 자모 단위 바이트로 쪼개기 때문에 훨씬 비싸다.)
    정확할 필요는 없다 — 컴팩션은 '넘치기 전에' 켜지면 되고, 어림이
    실제보다 조금 큰 쪽으로 틀리는 것이 안전하다.
    """
    if not text:
        return 0
    cjk = len(_CJK.findall(text))
    rest = len(text) - cjk
    return max(1, int(cjk / 1.5 + rest / 4) + 1)


@dataclass
class Message:
    role: str
    content: str = ""
    tool_name: str = ""
    tool_call_id: str = ""
    tool_args: dict = field(default_factory=dict)
    pinned: bool = False          # True 면 컴팩션이 건드리지 않는다

    def __post_init__(self) -> None:
        if self.role not in ROLES:
            raise ValueError(f"모르는 역할: {self.role!r}")

    @property
    def tokens(self) -> int:
        n = estimate_tokens(self.content) + estimate_tokens(self.tool_name)
        if self.tool_args:
            n += estimate_tokens(str(self.tool_args))
        return n + 4              # 역할·구분자 오버헤드

    def to_dict(self) -> dict:
        return {
            "role": self.role, "content": self.content,
            "tool_name": self.tool_name, "tool_call_id": self.tool_call_id,
            "tool_args": self.tool_args, "pinned": self.pinned,
        }

    @classmethod
    def from_dict(cls, raw: dict) -> "Message":
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in raw.items() if k in known})


Summarizer = Callable[[list[Message]], str]


def default_summarizer(dropped: list[Message]) -> str:
    """모델을 부르지 않는 요약 — 무엇이 있었는지 목록으로 남긴다.

    진짜 Code Puppy 는 여기서 작은 모델에 요약을 시킨다. 하지만 요약도
    실패할 수 있어서, 실패했을 때 돌아갈 자리로 이런 기계적 요약이 필요하다.
    """
    tools: list[str] = []
    users = 0
    for m in dropped:
        if m.role == "tool" and m.tool_name:
            if m.tool_name not in tools:
                tools.append(m.tool_name)
        elif m.role == "user":
            users += 1
    parts = [f"[요약] 이전 대화 {len(dropped)}건을 접었다."]
    if users:
        parts.append(f"사용자 요청 {users}건.")
    if tools:
        parts.append("쓴 도구: " + ", ".join(tools) + ".")
    return " ".join(parts)


class History:
    def __init__(self, system_prompt: str = "") -> None:
        self.messages: list[Message] = []
        if system_prompt:
            self.messages.append(Message("system", system_prompt, pinned=True))

    # ---- 쌓기 --------------------------------------------------------
    def add(self, msg: Message) -> Message:
        self.messages.append(msg)
        return msg

    def user(self, text: str) -> Message:
        return self.add(Message("user", text))

    def assistant(self, text: str, tool_name: str = "",
                  tool_call_id: str = "", tool_args: dict | None = None) -> Message:
        return self.add(Message("assistant", text, tool_name=tool_name,
                                tool_call_id=tool_call_id,
                                tool_args=dict(tool_args or {})))

    def tool_result(self, tool_call_id: str, tool_name: str, content: str) -> Message:
        return self.add(Message("tool", content, tool_name=tool_name,
                                tool_call_id=tool_call_id))

    # ---- 재기 --------------------------------------------------------
    def total_tokens(self) -> int:
        return sum(m.tokens for m in self.messages)

    def needs_compaction(self, window: int, threshold: float) -> bool:
        return self.total_tokens() > window * threshold

    def _protected_start(self, protected_tokens: int) -> int:
        """뒤에서부터 protected_tokens 를 채우는 첫 인덱스를 찾는다."""
        acc = 0
        idx = len(self.messages)
        for i in range(len(self.messages) - 1, -1, -1):
            acc += self.messages[i].tokens
            idx = i
            if acc >= protected_tokens:
                break
        return idx

    @staticmethod
    def _pull_back_to_pair(messages: list[Message], start: int) -> int:
        """start 가 도구 결과 한복판이면 그 짝(assistant 호출)까지 당긴다.

        assistant(tool_call) 없이 tool 결과만 남기면 모델 API 가 거부한다.
        경계를 앞으로 당겨서 짝을 통째로 살린다.
        """
        while start > 0 and messages[start].role == "tool":
            start -= 1
        return start

    def compact(self, protected_tokens: int,
                summarizer: Summarizer | None = None) -> tuple[int, str] | None:
        """중간 구간을 요약 한 줄로 접는다. 접은 게 없으면 None."""
        summarizer = summarizer or default_summarizer
        head = 0
        while head < len(self.messages) and self.messages[head].pinned:
            head += 1
        start = self._protected_start(protected_tokens)
        start = self._pull_back_to_pair(self.messages, start)
        if start <= head:
            return None                    # 접을 중간이 없다
        dropped = self.messages[head:start]
        if not dropped:
            return None
        summary = summarizer(dropped)
        note = Message("user", summary, pinned=True)
        self.messages[head:start] = [note]
        return len(dropped), summary

    # ---- 직렬화 ------------------------------------------------------
    def to_list(self) -> list[dict]:
        return [m.to_dict() for m in self.messages]

    @classmethod
    def from_list(cls, raw: Iterable[dict]) -> "History":
        h = cls()
        h.messages = [Message.from_dict(r) for r in raw]
        return h

    def __len__(self) -> int:
        return len(self.messages)
