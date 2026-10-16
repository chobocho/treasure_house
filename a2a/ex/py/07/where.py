# 이 부에서 쓰는 이름은 설치본의 어느 파일, 몇째 줄에 있는가.
#   python 07/where.py
# 소스를 열어 읽을 때의 길잡이다. 별명(alias)도 여기서 드러난다.
import inspect
from pathlib import Path

import a2a
from a2a.helpers import new_text_part
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import (
    create_agent_card_routes,
    create_jsonrpc_routes,
)
from a2a.server.tasks import InMemoryTaskStore, TaskUpdater
from a2a.types import Message, TaskState

ROOT = Path(a2a.__file__).parent.parent


# region: where
def where(name, obj):
    try:  # 파이썬으로 쓴 것은 파일과 줄이 있다
        path = Path(inspect.getsourcefile(obj)).relative_to(ROOT)
        line = inspect.getsourcelines(obj)[1]
        place = f"{path}:{line}"
    except TypeError:  # protobuf 가 만든 것은 소스가 없다
        d = obj.DESCRIPTOR
        place = f"{d.file.name} 의 {d.full_name} (생성됨)"
    real = getattr(obj, "__name__", name)
    alias = f"  ← 진짜 이름 {real}" if real != name else ""
    print(f"{name:<25}{place}{alias}")


# endregion

for name, obj in [
    ("Message", Message),
    ("TaskState", TaskState),
    ("new_text_part", new_text_part),
    ("AgentExecutor", AgentExecutor),
    ("RequestContext", RequestContext),
    ("EventQueue", EventQueue),
    ("TaskUpdater", TaskUpdater),
    ("DefaultRequestHandler", DefaultRequestHandler),
    ("InMemoryTaskStore", InMemoryTaskStore),
    ("create_jsonrpc_routes", create_jsonrpc_routes),
    ("create_agent_card_routes", create_agent_card_routes),
]:
    where(name, obj)
