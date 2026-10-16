# 요청 처리기를 HTTP 없이 직접 부른다 — 처리기가 하는 일만 떼어 보기.
#   python 07/direct.py
import asyncio

from a2a.helpers import new_data_part
from a2a.server.context import ServerCallContext
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    GetTaskRequest,
    ListTasksRequest,
    Message,
    Role,
    SendMessageConfiguration,
    SendMessageRequest,
    TaskState,
    UnsupportedOperationError,
)
from step2_task import QuoteExecutor, card


def request(n, now=False):
    req = {"date": "2026-10-30", "nights": 1, "headcount": n}
    msg = Message(
        message_id=f"m-{n}",
        role=Role.ROLE_USER,
        parts=[new_data_part(req)],
    )
    conf = SendMessageConfiguration(return_immediately=now)
    return SendMessageRequest(message=msg, configuration=conf)


def show(label, task):
    state = TaskState.Name(task.status.state)
    print(f"{label}: {state} 이력 {len(task.history)}", end="")
    print(f" 아티팩트 {len(task.artifacts)}")


# region: handler
store = InMemoryTaskStore()
handler = DefaultRequestHandler(
    agent_executor=QuoteExecutor(),
    task_store=store,
    agent_card=card("http://127.0.0.1:10700/"),
)
call = ServerCallContext()  # 누가 불렀나 — 여기서는 익명
# endregion


# region: calls
async def main():
    task = await handler.on_message_send(request(30), call)
    show("SendMessage (막는 호출)", task)
    got = await handler.on_get_task(GetTaskRequest(id=task.id), call)
    show("GetTask", got)
    quick = await handler.on_message_send(request(20, now=True), call)
    show("SendMessage (곧바로)", quick)
    await asyncio.sleep(0.5)  # 실행기는 뒤에서 마저 돈다
    show("0.5초 뒤 GetTask", await store.get(quick.id, call))
    page = await handler.on_list_tasks(ListTasksRequest(), call)
    print("ListTasks:", len(page.tasks), "개")
    try:
        async for _ in handler.on_message_send_stream(
            request(30), call
        ):
            pass
    except UnsupportedOperationError as e:
        print("스트림:", type(e).__name__, "—", e.message)


# endregion

asyncio.run(main())
