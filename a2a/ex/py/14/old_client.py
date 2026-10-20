# 카드가 판 0.3 문 하나만 적은 에이전트에 파이썬 SDK 로 묻는다.
# 따로 켤 것이 없다 — 팩토리가 카드의 판을 보고 옛 전송을 고른다.
#   python 14/old_client.py URL
import asyncio
import sys

from a2a.client import ClientConfig, create_client
from a2a.helpers import get_data_parts, new_data_part
from a2a.types import Message, Role, SendMessageRequest, TaskState


# region: send
async def main(url):
    client = await create_client(url, ClientConfig(streaming=False))
    req = {"date": "2026-10-30", "nights": 1, "headcount": 30}
    msg = Message(
        message_id="o-1",
        role=Role.ROLE_USER,
        parts=[new_data_part(req)],
    )
    async for ev in client.send_message(
        SendMessageRequest(message=msg)
    ):
        t = ev.task  # 옛 답도 v1.0 타입으로 바뀌어 온다
        quote = get_data_parts(t.artifacts[0].parts)[0]
        print(TaskState.Name(t.status.state), quote["venueName"])
    await client.close()


# endregion

asyncio.run(main(sys.argv[1]))
# @ norun
