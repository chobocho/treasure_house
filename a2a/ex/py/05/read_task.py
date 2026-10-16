# 끝난 숙소 Task 를 받아 필드를 하나씩 읽는다(파이썬 SDK 의 모양으로).
#   python 05/read_task.py 카드주소
import asyncio
import sys

from a2a.client import ClientConfig, create_client
from a2a.helpers.proto_helpers import new_data_part
from a2a.types import Message, Role, SendMessageRequest, TaskState

REQUEST = {"date": "2026-10-30", "nights": 1, "headcount": 30}


# region: read
def has(msg, field):
    # 메시지 필드는 없어도 빈 기본값을 준다 — 있는지는 HasField 로
    return "있음" if msg.HasField(field) else "없음"


def read(t):
    print("id        :", t.id)
    print("contextId :", t.context_id)
    st = t.status
    print("state     :", TaskState.Name(st.state))
    print(
        "timestamp :", type(st.timestamp).__name__, has(st, "timestamp")
    )
    print("message   :", has(st, "message"))
    for a in t.artifacts:
        kinds = [p.WhichOneof("content") for p in a.parts]
        print("artifact  :", a.name, kinds)
    for m in t.history:
        print("history   :", Role.Name(m.role), m.message_id)
    print("metadata  :", has(t, "metadata"))


# endregion


async def main(url):
    client = await create_client(url, ClientConfig(streaming=False))
    msg = Message(message_id="read-py", role=Role.ROLE_USER)
    msg.parts.append(new_data_part(REQUEST))
    async for ev in client.send_message(
        SendMessageRequest(message=msg)
    ):
        read(ev.task)
    await client.close()


asyncio.run(main(sys.argv[1]))
# @ norun
