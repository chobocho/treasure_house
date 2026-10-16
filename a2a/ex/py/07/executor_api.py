# 실행기를 쓰려면 무엇을 채워야 하나 — 설치본의 추상 클래스에 묻는다.
#   python 07/executor_api.py
import inspect
import typing

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import Event, EventQueue


# region: api
def short(t):
    if t is Event:  # 합집합 타입은 이름이 없어 별명으로
        return "Event"
    return getattr(t, "__name__", str(t))


def abstract(cls):
    print(f"{cls.__name__} — 채워야 할 추상 메서드:")
    for name in sorted(cls.__abstractmethods__):
        sig = inspect.signature(getattr(cls, name))
        args = ", ".join(
            f"{p.name}: {short(p.annotation)}"
            for p in sig.parameters.values()
            if p.name != "self"
        )
        print(f"  async def {name}({args})")


abstract(AgentExecutor)
abstract(EventQueue)
print("Event =", " | ".join(short(t) for t in typing.get_args(Event)))
props = [
    n
    for n, v in vars(RequestContext).items()
    if isinstance(v, property)
]
print("RequestContext 속성:", " ".join(sorted(props)))
# endregion
