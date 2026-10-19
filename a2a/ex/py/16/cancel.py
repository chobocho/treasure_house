# 교통 칸의 셋째 대본 — returnImmediately 로 맡기고, GetTask 로
# WORKING 을 본 뒤 CancelTask, 한 단계 넘게 기다렸다 다시 GetTask.
#   python 16/cancel.py 카드주소
import asyncio
import sys

from a2a.client import ClientConfig, create_client
from a2a.helpers.proto_helpers import new_data_part
from a2a.types import (
    CancelTaskRequest,
    GetTaskRequest,
    Message,
    Role,
    SendMessageConfiguration,
    SendMessageRequest,
    TaskState,
)

BUS = {"headcount": 30, "nights": 1, "depart": "강남역"}


def name(task):
    return TaskState.Name(task.status.state).removeprefix("TASK_STATE_")


# region: main
async def main(url):
    client = await create_client(url, ClientConfig(streaming=False))
    msg = Message(message_id="bus-cancel", role=Role.ROLE_USER)
    msg.parts.append(new_data_part(BUS))
    conf = SendMessageConfiguration(return_immediately=True)
    req = SendMessageRequest(message=msg, configuration=conf)
    async for ev in client.send_message(req):
        task = ev.task
    print("SendMessage →", name(task))
    while name(task) != "WORKING":  # 첫 단계가 시작될 때까지
        await asyncio.sleep(0.05)
        task = await client.get_task(GetTaskRequest(id=task.id))
    print("GetTask     →", name(task))
    task = await client.cancel_task(CancelTaskRequest(id=task.id))
    print("CancelTask  →", name(task))
    await asyncio.sleep(2.5)  # 한 단계(2초)보다 길게 기다린다
    task = await client.get_task(GetTaskRequest(id=task.id))
    print(
        "GetTask     →", name(task), f"아티팩트 {len(task.artifacts)}"
    )
    await client.close()


# endregion

asyncio.run(main(sys.argv[1]))
# @ norun
