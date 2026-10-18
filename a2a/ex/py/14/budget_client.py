# 예산 확장을 켜고 숙소 견적을 묻는 파이썬 SDK 클라이언트.
#   python 14/budget_client.py URL
import asyncio
import sys

import httpx
from a2a.client import (
    A2ACardResolver,
    ClientCallContext,
    ClientConfig,
    create_client,
)
from a2a.client.service_parameters import (
    ServiceParametersFactory,
    with_a2a_extensions,
)
from a2a.helpers import get_data_parts, new_data_part
from a2a.types import Message, Role, SendMessageRequest
from google.protobuf.json_format import MessageToDict

URI = "https://treasure-house.example/a2a/ext/budget/v1"


# region: send
async def main(url):
    async with httpx.AsyncClient() as http:
        card = await A2ACardResolver(http, url).get_agent_card()
    ext = [e for e in card.capabilities.extensions if e.uri == URI]
    print("카드:", "필수" if ext and ext[0].required else "선택")
    client = await create_client(card, ClientConfig(streaming=False))
    req = {"date": "2026-10-30", "nights": 1, "headcount": 30}
    msg = Message(
        message_id="b-1",
        role=Role.ROLE_USER,
        parts=[new_data_part(req)],
        extensions=[URI],  # 이 메시지에 확장의 데이터가 있다
    )
    msg.metadata.update({URI: {"limit": 2000000}})
    # 켜 달라는 요청은 메시지가 아니라 서비스 매개변수(머리글)로
    ups = [with_a2a_extensions([URI])]
    call = ClientCallContext(
        service_parameters=ServiceParametersFactory.create(ups)
    )
    send = SendMessageRequest(message=msg)
    async for ev in client.send_message(send, context=call):
        show(ev.task.artifacts[0])
    await client.close()


# endregion


# region: show
def show(art):
    total = get_data_parts(art.parts)[0]["total"]
    got = MessageToDict(art.metadata).get(URI)
    if got is None:
        print(f"견적 {total:,.0f}원 · 판정 없음")
        return
    verdict = "안" if got["within"] else "넘음"
    print(f"견적 {total:,.0f}원 · 상한 {got['limit']:,.0f}원 {verdict}")


# endregion

asyncio.run(main(sys.argv[1]))
# @ norun
