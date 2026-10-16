# 교통 에이전트에 같은 배차 요청을 두 번 — 막는 호출로 한 번,
# returnImmediately 로 한 번 — 보내고, 둘째는 GetTask 로 지켜본다.
#   python 05/modes.py 카드주소
import asyncio
import sys

from a2a.client import ClientConfig, create_client
from a2a.helpers.proto_helpers import new_data_part
from a2a.types import (
    GetTaskRequest,
    Message,
    Role,
    SendMessageConfiguration,
    SendMessageRequest,
    TaskState,
)

BUS = {"headcount": 30, "nights": 1, "depart": "강남역"}
DONE = ("COMPLETED", "FAILED", "CANCELED", "REJECTED")


def name(task):
    return TaskState.Name(task.status.state).removeprefix("TASK_STATE_")


# region: send
async def send(client, mid, now):
    msg = Message(message_id=mid, role=Role.ROLE_USER)
    msg.parts.append(new_data_part(BUS))
    # return_immediately 는 요청의 configuration 에 싣는다
    conf = SendMessageConfiguration(return_immediately=now)
    req = SendMessageRequest(message=msg, configuration=conf)
    async for ev in client.send_message(req):
        return ev.task  # 막는 호출이라 답은 하나


# endregion


# region: poll
async def poll(client, task_id):
    seen = None
    while (
        True
    ):  # 상태가 바뀔 때만 찍는다(몇 번 물었는지는 그때그때 다르다)
        task = await client.get_task(GetTaskRequest(id=task_id))
        if name(task) != seen:
            seen = name(task)
            print("  GetTask →", seen)
        if seen in DONE:
            return task
        await asyncio.sleep(0.1)


# endregion


async def main(url):
    client = await create_client(url, ClientConfig(streaming=False))
    task = await send(client, "bus-wait", now=False)
    print("막는 호출         →", name(task), len(task.artifacts))
    task = await send(client, "bus-now", now=True)
    print("returnImmediately →", name(task), len(task.artifacts))
    task = await poll(client, task.id)
    print("  아티팩트:", task.artifacts[0].name)
    await client.close()


asyncio.run(main(sys.argv[1]))
# @ norun
