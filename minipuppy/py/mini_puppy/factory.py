"""models.json 을 읽어 모델 객체를 만든다.

Code Puppy 의 model_factory.py 와 같은 자리. 요점은 **round_robin 이
type 값 하나로 들어간다**는 것이다. 특별 취급이 없다:

    {
      "gpt-4.1":   {"type": "openai", "url": "...", "model_id": "gpt-4.1"},
      "빠른-교대": {"type": "round_robin", "models": ["gpt-4.1", "sonnet"],
                    "rotate_every": 4}
    }

round_robin 안에 round_robin 을 넣어도 만들어진다 — 규약이 같으니까.
다만 자기 자신을 가리키면 무한 재귀라서, 만드는 중인 이름을 들고 다니며 막는다.
"""

from __future__ import annotations

import os

from .model import (HTTPModel, ModelReply, RoundRobinModel, ScriptedModel,
                    ToolCall)
from .session import read_json

BUILTIN_MODELS = {
    "scripted": {"type": "scripted", "replies": ["대본이 비었다."]},
}


class ModelConfigError(Exception):
    pass


def load_models(path) -> dict:
    """models.json 을 읽어 내장 정의 위에 얹는다."""
    got = read_json(path, default=None)
    merged = dict(BUILTIN_MODELS)
    if isinstance(got, dict):
        merged.update(got)
    return merged


def _env(value: str, environ: dict) -> str:
    """'$OPENAI_API_KEY' 처럼 적힌 값을 환경변수로 푼다.

    설정 파일에 키를 직접 적는 것을 막기 위한 것이다. 파일은 백업·git·
    화면 공유로 새기 쉽지만 환경변수는 덜하다.
    """
    if isinstance(value, str) and value.startswith("$"):
        return environ.get(value[1:], "")
    return value or ""


def build_model(name: str, defs: dict, environ: dict | None = None,
                _building: tuple = ()) -> object:
    environ = os.environ if environ is None else environ
    if name in _building:
        raise ModelConfigError("모델 정의가 자기 자신을 가리킨다: %s"
                               % " -> ".join(_building + (name,)))
    spec = defs.get(name)
    if spec is None:
        raise ModelConfigError("models.json 에 '%s' 가 없다. 있는 것: %s"
                               % (name, ", ".join(sorted(defs)) or "(없음)"))
    kind = spec.get("type", "openai")
    if kind == "scripted":
        return ScriptedModel(name, [_reply(r) for r in spec.get("replies", [])])
    if kind == "round_robin":
        members = spec.get("models") or []
        if not members:
            raise ModelConfigError("round_robin '%s' 에 models 가 비었다." % name)
        built = [build_model(m, defs, environ, _building + (name,))
                 for m in members]
        return RoundRobinModel(name, built,
                               rotate_every=int(spec.get("rotate_every", 1)),
                               cooldown=float(spec.get("cooldown", 30.0)))
    if kind in ("openai", "anthropic", "custom", "openai_compatible"):
        url = spec.get("url") or spec.get("base_url")
        if not url:
            raise ModelConfigError("'%s' 에 url 이 없다." % name)
        headers = {k: _env(v, environ)
                   for k, v in (spec.get("headers") or {}).items()}
        return HTTPModel(name, url=url,
                         api_key=_env(spec.get("api_key", ""), environ),
                         model_id=spec.get("model_id") or name,
                         timeout=int(spec.get("timeout", 120)),
                         headers=headers,
                         max_tokens=int(spec.get("max_tokens", 4096)))
    raise ModelConfigError("모르는 모델 종류: %r" % kind)


def _reply(raw):
    """대본 한 줄을 ModelReply 로. 문자열이면 그냥 말, dict 면 도구 호출.

        "다 됐다"                                     -> 말
        {"tool": "read_file", "args": {"path": "a"}}  -> 도구 호출 한 건
        {"tools": [{...}, {...}]}                     -> 한 번에 여러 건
        {"text": "고쳤다"}                             -> 말(명시형)

    네트워크 없이 실행 루프 전체를 시연·검증하기 위한 장치다.
    """
    if isinstance(raw, str):
        return ModelReply(text=raw)
    if not isinstance(raw, dict):
        return ModelReply(text=str(raw))
    items = raw.get("tools")
    if items is None and raw.get("tool"):
        items = [{"tool": raw["tool"], "args": raw.get("args", {})}]
    calls = []
    for i, item in enumerate(items or []):
        calls.append(ToolCall(id=item.get("id") or ("s%d" % i),
                              name=item.get("tool", ""),
                              args=item.get("args") or {}))
    return ModelReply(text=raw.get("text", ""), tool_calls=calls)
