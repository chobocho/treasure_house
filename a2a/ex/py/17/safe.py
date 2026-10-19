# 끊긴 SendMessage 를 다시 보내지 않고, 맥락으로 찾아 다시 붙는다.
#   python 17/safe.py 카드주소
import asyncio
import sys

from a2a.client import ClientCallContext, ClientConfig, create_client
from a2a.client.errors import A2AClientTimeoutError
from a2a.helpers.proto_helpers import new_data_part
from a2a.types import (
    ListTasksRequest,
    Message,
    Role,
    SendMessageRequest,
    SubscribeToTaskRequest,
    TaskState,
)

BUS = {"headcount": 30, "nights": 1, "depart": "강남역"}
CTX = "ctx-safe"  # 보내기 전에 맥락을 정해 둔다 — 찾을 열쇠


def name(task):
    return TaskState.Name(task.status.state).removeprefix("TASK_STATE_")


# region: main
async def main(url):
    once = await create_client(url, ClientConfig(streaming=False))
    msg = Message(message_id="m-safe", role=Role.ROLE_USER)
    msg.context_id = CTX
    msg.parts.append(new_data_part(BUS))
    short = ClientCallContext(timeout=1.5)
    try:
        req = SendMessageRequest(message=msg)
        async for _ in once.send_message(req, context=short):
            pass
    except A2AClientTimeoutError:
        print("① 1.5초에 끊김 — 다시 보내지 않는다")
    page = await once.list_tasks(ListTasksRequest(context_id=CTX))
    task = page.tasks[0]
    print(f"② ListTasks(contextId) → {len(page.tasks)}건 {name(task)}")
    # 파이썬 SDK 의 구독은 streaming=True 클라이언트에서만 된다
    sub = await create_client(url, ClientConfig(streaming=True))
    seen = []
    async for ev in sub.subscribe(SubscribeToTaskRequest(id=task.id)):
        seen.append(ev)
    first, last = seen[0].task, seen[-1].status_update
    print(f"③ SubscribeToTask → 처음 {name(first)} … 끝 {name(last)}")
    page = await once.list_tasks(ListTasksRequest(context_id=CTX))
    now = name(page.tasks[0])
    print(f"④ ListTasks(contextId) → {len(page.tasks)}건 {now}")


# endregion

asyncio.run(main(sys.argv[1]))
# @ norun
