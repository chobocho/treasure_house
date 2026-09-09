"""도구 등록기 — 파이썬 함수를 모델이 부를 수 있는 것으로 바꾸는 층.

세 가지 일을 한다.
  1. 함수 서명과 타입 힌트에서 JSON 스키마를 뽑는다 (모델에 보낼 도구 설명).
  2. 에이전트별 **허용 목록**으로 거른다 — 목록에 없는 도구는 스키마에도
     안 나가고, 우겨서 불러도 거부된다. "도구 목록이 곧 가드레일"의 실물.
  3. 모델이 보낸 인자를 **강제로 형 맞춤**한다. 모델은 3 을 "3" 으로,
     true 를 "true" 로 보내는 일이 잦다. 여기서 안 고치면 도구 안에서
     TypeError 가 터지고, 모델은 그 오류를 이해하지 못해 같은 실수를 반복한다.
"""

from __future__ import annotations

import inspect
import json
from dataclasses import dataclass, field
from typing import Any, Callable, get_args, get_origin

TRUE = {"1", "true", "yes", "on", "y"}
FALSE = {"0", "false", "no", "off", "n"}


class ToolError(Exception):
    """도구가 사람이 읽을 수 있는 이유로 실패했다. 모델에게 그대로 돌려준다."""


@dataclass
class ToolResult:
    ok: bool
    content: str
    truncated: bool = False
    meta: dict = field(default_factory=dict)


_PY_TO_JSON = {str: "string", int: "integer", float: "number",
               bool: "boolean", list: "array", dict: "object"}


def _json_type(annotation: Any) -> str:
    if annotation is inspect.Parameter.empty:
        return "string"
    origin = get_origin(annotation)
    if origin is not None:
        args = [a for a in get_args(annotation) if a is not type(None)]
        if len(args) == 1:
            return _json_type(args[0])
        return _PY_TO_JSON.get(origin, "string")
    return _PY_TO_JSON.get(annotation, "string")


def coerce(value: Any, annotation: Any) -> Any:
    """모델이 보낸 값을 파이썬 타입으로 끌어당긴다. 못 하면 ToolError."""
    if annotation is inspect.Parameter.empty or annotation is Any:
        return value
    origin = get_origin(annotation)
    if origin is not None:
        args = [a for a in get_args(annotation) if a is not type(None)]
        if value is None:
            return None
        if len(args) == 1:
            return coerce(value, args[0])
        return value
    if annotation is bool:
        if isinstance(value, bool):
            return value
        s = str(value).strip().lower()
        if s in TRUE:
            return True
        if s in FALSE:
            return False
        raise ToolError("참/거짓으로 읽을 수 없는 값: %r" % (value,))
    if annotation is int:
        if isinstance(value, bool):
            return int(value)
        try:
            return int(str(value).strip())
        except (TypeError, ValueError):
            raise ToolError("정수로 읽을 수 없는 값: %r" % (value,))
    if annotation is float:
        try:
            return float(str(value).strip())
        except (TypeError, ValueError):
            raise ToolError("실수로 읽을 수 없는 값: %r" % (value,))
    if annotation is str:
        if isinstance(value, str):
            return value
        if isinstance(value, (dict, list)):
            return json.dumps(value, ensure_ascii=False)
        return str(value)
    if annotation in (list, dict):
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                raise ToolError("JSON 으로 읽을 수 없는 값: %r" % (value,))
        return value
    return value


@dataclass
class Tool:
    name: str
    fn: Callable
    description: str
    params: dict
    required: list

    def schema(self) -> dict:
        props = {}
        for pname, (ann, _default, desc) in self.params.items():
            entry = {"type": _json_type(ann)}
            if desc:
                entry["description"] = desc
            props[pname] = entry
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {"type": "object", "properties": props,
                           "required": list(self.required)},
        }


def _param_docs(doc: str) -> dict:
    """docstring 의 '이름: 설명' 줄을 인자 설명으로 걷는다."""
    out = {}
    in_args = False
    for line in (doc or "").splitlines():
        stripped = line.strip()
        if stripped in ("Args:", "인자:"):
            in_args = True
            continue
        if in_args:
            if not stripped:
                continue
            if ":" not in stripped or not line.startswith((" ", "\t")):
                break
            key, _, val = stripped.partition(":")
            key = key.strip()
            if key.replace("_", "").isalnum():
                out[key] = val.strip()
    return out


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict = {}

    def register(self, fn=None, *, name=None):
        """@reg.register 또는 @reg.register(name="...") 둘 다 된다."""
        def wrap(func):
            doc = inspect.getdoc(func) or ""
            summary = doc.split("\n\n")[0].strip() or func.__name__
            docs = _param_docs(doc)
            sig = inspect.signature(func)
            params, required = {}, []
            for pname, p in sig.parameters.items():
                if pname == "ctx":
                    continue          # 실행 문맥은 모델에 안 보인다
                params[pname] = (p.annotation, p.default, docs.get(pname, ""))
                if p.default is inspect.Parameter.empty:
                    required.append(pname)
            self._tools[name or func.__name__] = Tool(
                name=name or func.__name__, fn=func, description=summary,
                params=params, required=required)
            return func
        return wrap(fn) if fn is not None else wrap

    def names(self) -> list:
        return sorted(self._tools)

    def get(self, name: str):
        return self._tools.get(name)

    def allowed(self, allowlist) -> list:
        if allowlist is None:
            return [self._tools[n] for n in self.names()]
        keep = set(allowlist)
        return [self._tools[n] for n in self.names() if n in keep]

    def schemas(self, allowlist=None) -> list:
        return [t.schema() for t in self.allowed(allowlist)]

    def call(self, name: str, args: dict, ctx=None, allowlist=None,
             max_output: int = 8000) -> ToolResult:
        if allowlist is not None and name not in set(allowlist):
            return ToolResult(False, "이 에이전트에는 '%s' 도구가 없다." % name)
        tool = self._tools.get(name)
        if tool is None:
            close = [n for n in self.names() if n.startswith(name[:3])]
            hint = (" 비슷한 것: " + ", ".join(close)) if close else ""
            return ToolResult(False, "모르는 도구: '%s'.%s" % (name, hint))
        kwargs = {}
        try:
            for pname, (ann, default, _d) in tool.params.items():
                if pname in args:
                    kwargs[pname] = coerce(args[pname], ann)
                elif default is inspect.Parameter.empty:
                    raise ToolError("'%s' 인자가 빠졌다." % pname)
            if "ctx" in inspect.signature(tool.fn).parameters:
                kwargs["ctx"] = ctx
            out = tool.fn(**kwargs)
        except ToolError as exc:
            return ToolResult(False, str(exc))
        except Exception as exc:      # 도구 사고가 에이전트를 죽이지 않게
            return ToolResult(False, "%s: %s" % (type(exc).__name__, exc))
        if isinstance(out, str):
            text = out
        else:
            text = json.dumps(out, ensure_ascii=False, indent=2, default=str)
        if len(text) > max_output:
            keep = max_output // 2
            cut = len(text) - max_output
            text = text[:keep] + "\n… [%d자 잘림] …\n" % cut + text[-keep:]
            return ToolResult(True, text, truncated=True)
        return ToolResult(True, text)
