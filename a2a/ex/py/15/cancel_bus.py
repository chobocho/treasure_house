# 달리는 배차를 남이 취소하면 — 기획 에이전트에 이야기를 보내 두고,
# 교통 에이전트에 맡겨진 배차가 첫 단계를 알리면 그 작업에 CancelTask
# 를 보낸다. 기획 에이전트가 그 취소를 자기 사용자에게 어떻게 넘기는지
# 본다. 출력은 둘 다 끝난 뒤 정한 차례로 찍는다(취소 → 기획의 스트림).
#   python 15/cancel_bus.py 기획URL 교통URL
import asyncio
import sys

from a2a.client import ClientConfig, create_client
from a2a.helpers import get_message_text
from a2a.helpers.proto_helpers import new_text_part
from a2a.types import (
    CancelTaskRequest,
    ListTasksRequest,
    Message,
    Role,
    SendMessageRequest,
    TaskState,
)

from agents.ask import show

STORY = (
    "2026-10-30부터 1박 2일, 30명(채식 2명), "
    "예산 6,000,000원, 출발 강남역"
)


async def tell(url):
    """이야기를 스트림으로 보내고 받은 이벤트를 모아 둔다."""
    client = await create_client(url)
    msg = Message(
        role=Role.ROLE_USER,
        parts=[new_text_part(STORY)],
        message_id="ask-0",
    )
    req = SendMessageRequest(message=msg)
    events = [ev async for ev in client.send_message(req)]
    await client.close()
    return events


# region: cancel
async def cancel_first_step(url):
    """첫 단계("배차 요청 접수")를 알린 배차를 찾아 취소한다."""
    client = await create_client(url, ClientConfig(streaming=False))
    want = ListTasksRequest(status=TaskState.TASK_STATE_WORKING)
    while True:  # 시간이 아니라 상태를 기다린다
        tasks = (await client.list_tasks(want)).tasks
        hit = [
            t
            for t in tasks
            if get_message_text(t.status.message) == "배차 요청 접수"
        ]
        if hit:
            break
        await asyncio.sleep(0.05)
    task = await client.cancel_task(CancelTaskRequest(id=hit[0].id))
    await client.close()
    return task


async def main(planner, bus):
    story = asyncio.create_task(tell(planner))
    task = await cancel_first_step(bus)
    print("CancelTask →", TaskState.Name(task.status.state))
    for ev in await story:
        show(ev)


# endregion

asyncio.run(main(*sys.argv[1:]))
# @ norun
