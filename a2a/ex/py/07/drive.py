# 실행기를 서버 없이 돌려 본다 — 들어온 이벤트를 찍기만 하는 큐로.
#   python 07/drive.py echo 글
#   python 07/drive.py quote 날짜 박수 인원
import asyncio
import sys

from a2a.helpers import (
    get_data_parts,
    get_message_text,
    new_data_part,
    new_text_part,
)
from a2a.server.agent_execution import RequestContext
from a2a.server.context import ServerCallContext
from a2a.server.events import EventQueue
from a2a.types import Message, Role, SendMessageRequest, TaskState
from step1_echo import EchoExecutor
from step2_task import QuoteExecutor


def describe(ev):
    name = type(ev).__name__
    if name == "Message":
        return f"Message {Role.Name(ev.role)}: {get_message_text(ev)}"
    if name == "Task":
        state = TaskState.Name(ev.status.state)
        return f"Task {ev.id} {state} 이력 {len(ev.history)}"
    if name == "TaskStatusUpdateEvent":
        said = get_message_text(ev.status.message)
        return f"상태 {TaskState.Name(ev.status.state)} {said}".strip()
    data = get_data_parts(ev.artifact.parts)[0]
    return f"아티팩트 {ev.artifact.name}: {data['venueName']}"


# region: queue
class PrintQueue(EventQueue):
    """EventQueue 의 하위 클래스 — enqueue_event 하나만 채우면 된다."""

    async def enqueue_event(self, event):
        print("  →", describe(event))


# endregion


# region: context
def context_for(args):
    if len(args) == 3:  # 날짜 박수 인원 → DataPart
        date, nights, n = args
        req = {"date": date, "nights": int(nights), "headcount": int(n)}
        part = new_data_part(req)
    else:
        part = new_text_part(args[0])
    msg = Message(message_id="m-1", role=Role.ROLE_USER, parts=[part])
    ctx = RequestContext(
        ServerCallContext(), SendMessageRequest(message=msg)
    )
    print("task_id   ", ctx.task_id)
    print("context_id", ctx.context_id)
    print("이어 말하기?", ctx.current_task is not None)
    return ctx


# endregion

# region: main
executor = {"echo": EchoExecutor, "quote": QuoteExecutor}[sys.argv[1]]
ctx = context_for(sys.argv[2:])
asyncio.run(executor().execute(ctx, PrintQueue()))
# endregion
# @ norun
