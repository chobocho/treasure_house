"""에이전트 등록기 — 인격을 고르고 갈아 끼우는 층.

에이전트 하나 = (이름, 시스템 프롬프트, 도구 허용 목록, 모델).
그게 전부다. 그래서 **JSON 파일 하나로 새 인격을 만들 수 있다.**

    ~/.mini_puppy/agents/python-tutor.json
    {"name":"python-tutor", "system_prompt":["너는 파이썬 튜터다."],
     "tools":["list_files","read_file","grep"]}

이 튜터에는 write_file 도 edit_file 도 없다. 프롬프트를 아무리 구슬려도
코드를 못 고친다 — 스키마에 그 도구가 아예 없기 때문이다.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from .agent import Agent
from .session import read_json

NAME_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,39}$")

READ_ONLY = ["list_files", "read_file", "grep"]
FULL = ["list_files", "read_file", "grep", "write_file", "edit_file",
        "run_command"]


@dataclass
class AgentSpec:
    name: str
    system_prompt: str = ""
    display_name: str = ""
    description: str = ""
    tools: list | None = None
    model: str = ""
    source: str = "builtin"

    def __post_init__(self) -> None:
        if not NAME_RE.match(self.name or ""):
            raise ValueError("에이전트 이름은 소문자·숫자·-·_ 로 40자까지: %r"
                             % self.name)
        self.display_name = self.display_name or self.name

    @classmethod
    def from_dict(cls, raw: dict, source: str = "json") -> "AgentSpec":
        prompt = raw.get("system_prompt", "")
        if isinstance(prompt, list):
            prompt = "\n".join(str(p) for p in prompt)
        tools = raw.get("tools")
        if isinstance(tools, str):
            tools = [t.strip() for t in tools.split(",") if t.strip()]
        return cls(name=raw.get("name", ""), system_prompt=prompt,
                   display_name=raw.get("display_name", ""),
                   description=raw.get("description", ""),
                   tools=tools, model=raw.get("model", ""), source=source)


BUILTIN = [
    AgentSpec(
        name="mini-puppy", display_name="Mini Puppy 🐶",
        description="코드를 읽고 고치는 기본 에이전트",
        system_prompt=(
            "너는 mini-puppy, 명령줄에서 도는 코딩 에이전트다.\n"
            "- 먼저 읽고 나서 고친다. 파일을 안 보고 추측하지 마라.\n"
            "- 한 번에 한 가지만 바꾼다. 큰 덩어리로 덮어쓰지 마라.\n"
            "- 고친 뒤에는 시험을 돌려 확인한다.\n"
            "- 모르면 모른다고 말한다."),
        tools=FULL),
    AgentSpec(
        name="reader", display_name="Reader 📖",
        description="읽기만 한다. 아무것도 못 고친다",
        system_prompt=("너는 코드를 읽고 설명하는 에이전트다.\n"
                       "고칠 방법을 말로 알려 주되, 직접 고치지는 않는다."),
        tools=READ_ONLY),
    AgentSpec(
        name="tester", display_name="Tester 🧪",
        description="시험을 돌리고 실패를 보고한다",
        system_prompt=("너는 시험을 돌려 결과를 정리하는 에이전트다.\n"
                       "실패한 시험의 이름과 이유를 짧게 추린다."),
        tools=READ_ONLY + ["run_command"]),
]


class AgentRegistry:
    def __init__(self, agents_dir=None) -> None:
        self.dir = Path(agents_dir) if agents_dir else None
        self.specs: dict = {s.name: s for s in BUILTIN}
        self.errors: list = []
        self.reload()

    def reload(self) -> None:
        self.specs = {s.name: s for s in BUILTIN}
        self.errors = []
        if self.dir is None or not self.dir.is_dir():
            return
        for path in sorted(self.dir.glob("*.json")):
            raw = read_json(path)
            if not isinstance(raw, dict):
                self.errors.append("%s: JSON 이 깨졌다" % path.name)
                continue
            raw.setdefault("name", path.stem)
            try:
                spec = AgentSpec.from_dict(raw, source=str(path))
            except ValueError as exc:
                self.errors.append("%s: %s" % (path.name, exc))
                continue
            self.specs[spec.name] = spec      # 파일이 내장을 덮는다

    def names(self) -> list:
        return sorted(self.specs)

    def get(self, name: str) -> AgentSpec | None:
        return self.specs.get(name)

    def describe(self) -> str:
        rows = []
        for name in self.names():
            s = self.specs[name]
            mark = "내장" if s.source == "builtin" else "파일"
            tools = "전부" if s.tools is None else "%d개" % len(s.tools)
            rows.append("%-14s %-4s 도구 %-4s %s"
                        % (name, mark, tools, s.description))
        return "\n".join(rows)

    def build(self, name: str, model, tool_registry, bus=None,
              config=None) -> Agent:
        spec = self.get(name)
        if spec is None:
            raise KeyError("모르는 에이전트: %s (있는 것: %s)"
                           % (name, ", ".join(self.names())))
        unknown = [] if spec.tools is None else [
            t for t in spec.tools if tool_registry.get(t) is None]
        if unknown:
            raise KeyError("'%s' 가 없는 도구를 요구한다: %s"
                           % (name, ", ".join(unknown)))
        return Agent(name=spec.name, display_name=spec.display_name,
                     system_prompt=spec.system_prompt, model=model,
                     registry=tool_registry, tools=spec.tools, bus=bus,
                     config=config)


def register_subagent_tool(tool_registry, agent_registry, model_for,
                           bus=None, config=None, max_depth: int = 3):
    """에이전트를 도구로 노출한다. 깊이 제한이 유일한 안전장치다.

    이것이 없으면 에이전트가 자기 자신을 부르고, 그것이 또 자기를 불러
    토큰을 순식간에 태운다. Code Puppy 도 같은 이유로 재귀 깊이를 센다.
    """

    @tool_registry.register
    def invoke_agent(ctx, agent: str, task: str) -> str:
        """다른 에이전트에게 일을 맡기고 결과만 받는다.

        Args:
          agent: 에이전트 이름
          task: 맡길 일을 한 문단으로
        """
        from .tools import ToolError
        depth = getattr(ctx, "depth", 0) + 1
        if depth > max_depth:
            raise ToolError("서브에이전트 깊이 한계(%d)를 넘었다." % max_depth)
        spec = agent_registry.get(agent)
        if spec is None:
            raise ToolError("모르는 에이전트: %s (있는 것: %s)"
                            % (agent, ", ".join(agent_registry.names())))
        sub = agent_registry.build(agent, model_for(spec), tool_registry,
                                   bus=bus, config=config)
        child = _child_ctx(ctx, depth)
        result, _hist = sub.run(task, ctx=child, max_steps=12, depth=depth)
        # 자식의 대화 기록은 넘기지 않는다. **결과만** 부모 컨텍스트에 들어간다 —
        # 이것이 서브에이전트가 컨텍스트를 아끼는 원리다.
        return "[%s] %s\n(걸음 %d, 도구 %d회)" % (
            agent, result.text, result.steps, result.tool_calls)

    return tool_registry


def _child_ctx(ctx, depth: int):
    import copy
    child = copy.copy(ctx)
    try:
        child.depth = depth
    except AttributeError:
        pass
    return child
