# 배차 하나를 끝까지 맡긴 뒤, 같은 작업을 historyLength 만 바꿔
# 여러 번 GetTask 한다. 이력이 몇 개, 어떤 것이 오는지 찍는다.
#   python 05/history.py 카드주소
import asyncio
import sys

from a2a.client import ClientConfig, create_client
from a2a.helpers.proto_helpers import get_message_text, new_data_part
from a2a.types import (
    GetTaskRequest,
    Message,
    Role,
    SendMessageRequest,
)
from a2a.utils.errors import A2AError

BUS = {"headcount": 30, "nights": 1, "depart": "강남역"}


def line(task):
    said = [get_message_text(m) or "(데이터)" for m in task.history]
    return f"{len(said)}개 {' / '.join(said)}".rstrip()


# region: history
async def main(url):
    client = await create_client(url, ClientConfig(streaming=False))
    msg = Message(message_id="bus-h", role=Role.ROLE_USER)
    msg.parts.append(new_data_part(BUS))
    async for ev in client.send_message(
        SendMessageRequest(message=msg)
    ):
        task_id = ev.task.id  # 막는 호출 — COMPLETED 를 받는다
    print(
        "없음 →",
        line(await client.get_task(GetTaskRequest(id=task_id))),
    )
    for n in (0, 1, 2, 10, -1):
        # history_length 는 optional — 0 을 넣으면 "0 을 줬다" 가 된다
        req = GetTaskRequest(id=task_id, history_length=n)
        try:
            print(f"{n:>4} →", line(await client.get_task(req)))
        except A2AError as e:  # 서버가 오류로 답하면
            print(f"{n:>4} → 오류 {type(e).__name__}: {e}")
    await client.close()


# endregion

asyncio.run(main(sys.argv[1]))
# @ norun
