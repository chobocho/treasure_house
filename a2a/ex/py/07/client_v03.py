# 카드의 인터페이스가 v0.3 이라고 하면 파이썬 클라이언트는 무엇을
# 보내나. 진짜 카드를 받아 protocol_version 만 "0.3" 으로 고친다.
#   python 07/client_v03.py URL
import asyncio
import sys

import httpx
from a2a.client import A2ACardResolver, ClientConfig, create_client
from a2a.helpers import get_data_parts, new_data_part
from a2a.types import Message, Role, SendMessageRequest, TaskState


# region: v03
async def main(url):
    async with httpx.AsyncClient() as http:
        card = await A2ACardResolver(http, url).get_agent_card()
    card.supported_interfaces[0].protocol_version = "0.3"
    config = ClientConfig(streaming=False)
    client = await create_client(card, config)  # 공장이 전송을 고른다
    req = {"date": "2026-10-30", "nights": 1, "headcount": 30}
    msg = Message(
        message_id="v03-2",
        role=Role.ROLE_USER,
        parts=[new_data_part(req)],
    )
    async for ev in client.send_message(
        SendMessageRequest(message=msg)
    ):
        t = ev.task  # 받은 것은 v1.0 타입으로 바뀌어 온다
        quote = get_data_parts(t.artifacts[0].parts)[0]
        print(TaskState.Name(t.status.state), quote["venueName"])
    await client.close()


# endregion

asyncio.run(main(sys.argv[1]))
# @ norun
