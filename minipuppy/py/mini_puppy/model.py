"""모델 층 — 대화 기록과 도구 목록을 넣으면 답과 도구 호출이 나오는 상자.

세 가지 구현이 있다.
  ScriptedModel   — 대본대로 답한다. 시험과 시연에 쓴다(네트워크 없음).
  HTTPModel       — OpenAI 호환 /chat/completions 를 부른다. 실물.
  RoundRobinModel — 여러 모델을 돌려 쓴다. Code Puppy 의 핵심 발상 —
                    round_robin 은 특별 기능이 아니라 **모델의 한 종류**다.
                    아래 클래스가 Model 규약을 그대로 따르는 것이 그 증거다.

rotate_every 가 저울질하는 것:
  1  — 요청마다 바꾼다. 부하는 가장 고르지만 프롬프트 캐시가 매번 깨진다.
  N  — N 번에 한 번 바꾼다. 같은 엔드포인트로 연달아 가서 캐시가 산다.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field


@dataclass
class ToolCall:
    id: str
    name: str
    args: dict = field(default_factory=dict)


@dataclass
class ModelReply:
    text: str = ""
    tool_calls: list = field(default_factory=list)
    usage: dict = field(default_factory=dict)
    model: str = ""

    @property
    def wants_tools(self) -> bool:
        return bool(self.tool_calls)


class ModelError(Exception):
    """모델 호출이 실패했다. 재시도 판단은 부르는 쪽이 한다."""

    def __init__(self, message: str, retryable: bool = False) -> None:
        super().__init__(message)
        self.retryable = retryable


class ScriptedModel:
    """미리 정한 답을 순서대로 내놓는다.

    시험이 진짜 모델을 부르면 느리고, 비싸고, 매번 다른 답이 나와서
    무엇을 검사하는지 알 수 없게 된다. 대본 모델은 **실행 루프만** 검사한다.
    """

    def __init__(self, name: str, replies: list) -> None:
        self.name = name
        self.replies = list(replies)
        self.calls: list = []          # 무엇을 봤는지 기록 (시험이 검사한다)
        self.index = 0

    def complete(self, messages: list, tools: list) -> ModelReply:
        self.calls.append({"messages": [dict(m) for m in messages],
                           "tools": [t["name"] for t in tools]})
        if self.index >= len(self.replies):
            return ModelReply(text="(대본 끝)", model=self.name)
        reply = self.replies[self.index]
        self.index += 1
        if isinstance(reply, str):
            reply = ModelReply(text=reply)
        reply.model = self.name
        return reply

    def reset(self) -> None:
        self.index = 0
        self.calls.clear()


class HTTPModel:
    """OpenAI 호환 엔드포인트. 표준 라이브러리 urllib 만 쓴다."""

    def __init__(self, name: str, url: str, api_key: str = "",
                 model_id: str = "", timeout: int = 120,
                 headers: dict | None = None, max_tokens: int = 4096) -> None:
        self.name = name
        self.url = url.rstrip("/")
        self.api_key = api_key
        self.model_id = model_id or name
        self.timeout = timeout
        self.extra_headers = dict(headers or {})
        self.max_tokens = max_tokens

    def _payload(self, messages: list, tools: list) -> dict:
        body = {"model": self.model_id, "messages": messages,
                "max_tokens": self.max_tokens}
        if tools:
            body["tools"] = [{"type": "function", "function": t} for t in tools]
        return body

    def complete(self, messages: list, tools: list) -> ModelReply:
        data = json.dumps(self._payload(messages, tools)).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = "Bearer " + self.api_key
        headers.update(self.extra_headers)
        req = urllib.request.Request(self.url + "/chat/completions",
                                     data=data, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            # 429·5xx 는 다시 걸어 볼 만하다. 4xx 는 고쳐야 할 우리 잘못이다.
            retryable = exc.code == 429 or 500 <= exc.code < 600
            raise ModelError("HTTP %d: %s" % (exc.code, exc.reason), retryable)
        except (urllib.error.URLError, TimeoutError) as exc:
            raise ModelError("연결 실패: %s" % exc, retryable=True)
        return self.parse(raw)

    def parse(self, raw: dict) -> ModelReply:
        try:
            choice = raw["choices"][0]["message"]
        except (KeyError, IndexError, TypeError):
            raise ModelError("모르는 응답 모양: %s" % json.dumps(raw)[:200])
        calls = []
        for i, tc in enumerate(choice.get("tool_calls") or []):
            fn = tc.get("function", {})
            args = fn.get("arguments", "{}")
            if isinstance(args, str):
                try:
                    args = json.loads(args or "{}")
                except json.JSONDecodeError:
                    args = {"__raw": args}   # 모델이 깨진 JSON 을 보낼 때가 있다
            calls.append(ToolCall(id=tc.get("id") or "call_%d" % i,
                                  name=fn.get("name", ""), args=args or {}))
        return ModelReply(text=choice.get("content") or "", tool_calls=calls,
                          usage=raw.get("usage") or {}, model=self.name)


class RoundRobinModel:
    """여러 모델을 번갈아 쓴다. 규약은 다른 모델과 똑같다."""

    def __init__(self, name: str, models: list, rotate_every: int = 1,
                 cooldown: float = 30.0, clock=time.monotonic) -> None:
        if not models:
            raise ValueError("돌릴 모델이 없다.")
        self.name = name
        self.models = list(models)
        self.rotate_every = max(1, int(rotate_every))
        self.cooldown = cooldown
        self.clock = clock
        self.cursor = 0
        self.used = 0                    # 지금 모델로 몇 번 썼나
        self.down: dict = {}             # 이름 -> 쉬는 게 끝나는 시각
        self.picks: list = []            # 누구를 골랐는지 기록

    def _healthy(self, model) -> bool:
        until = self.down.get(model.name)
        return until is None or self.clock() >= until

    def pick(self):
        """지금 쓸 모델. 아픈 놈은 건너뛴다."""
        if self.used >= self.rotate_every:
            self.cursor = (self.cursor + 1) % len(self.models)
            self.used = 0
        n = len(self.models)
        for step in range(n):
            candidate = self.models[(self.cursor + step) % n]
            if self._healthy(candidate):
                if step:                 # 아픈 놈을 건너뛰었으면 커서도 옮긴다
                    self.cursor = (self.cursor + step) % n
                    self.used = 0
                return candidate
        # 전부 아프면 가장 빨리 낫는 놈으로 그냥 간다 — 멈추는 것보단 낫다
        return min(self.models, key=lambda m: self.down.get(m.name, 0))

    def complete(self, messages: list, tools: list) -> ModelReply:
        model = self.pick()
        self.picks.append(model.name)
        try:
            reply = model.complete(messages, tools)
        except ModelError as exc:
            if exc.retryable:
                self.down[model.name] = self.clock() + self.cooldown
                self.used = self.rotate_every    # 다음엔 다른 놈으로
            raise
        self.used += 1
        return reply
