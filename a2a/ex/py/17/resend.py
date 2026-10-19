# 시간 초과 뒤 같은 messageId 로 다시 보내면 — 작업이 둘 생긴다.
#   python 17/resend.py 카드주소
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
    TaskState,
)

BUS = {"headcount": 30, "nights": 1, "depart": "강남역"}
CTX = "ctx-resend"  # 나중에 ListTasks 로 거르려고 맥락을 정해 둔다


def name(task):
    return TaskState.Name(task.status.state).removeprefix("TASK_STATE_")


# region: send
async def send(client, seconds):
    msg = Message(message_id="m-resend", role=Role.ROLE_USER)
    msg.context_id = CTX
    msg.parts.append(new_data_part(BUS))
    call = ClientCallContext(timeout=seconds)  # 이 호출만의 제한
    req = SendMessageRequest(message=msg)
    async for ev in client.send_message(req, context=call):
        return ev.task


# endregion


async def main(url):
    client = await create_client(url, ClientConfig(streaming=False))
    try:
        await send(client, 1.5)
    except A2AClientTimeoutError as e:
        print("① 1.5초 제한 →", type(e).__name__, e)
    task = await send(client, 10)
    print("② 같은 messageId 로 다시 →", name(task))
    page = await client.list_tasks(ListTasksRequest(context_id=CTX))
    print(f"③ ListTasks(contextId) → {len(page.tasks)}건")
    for t in page.tasks:
        print("  ", name(t), "첫 메시지", t.history[0].message_id)
    await client.close()


asyncio.run(main(sys.argv[1]))
# @ norun
