# 다시 해도 되는 실패만, 간격을 두 배씩 늘려 다시 한다.
#   python 17/retry.py 카드주소 죽은주소
import asyncio
import sys

import httpx
from a2a.client import (
    A2ACardResolver,
    ClientCallContext,
    ClientConfig,
    create_client,
)
from a2a.helpers.proto_helpers import new_data_part
from a2a.types import GetTaskRequest, Message, Role, SendMessageRequest
from a2a.utils.errors import A2AError

BUS = {"headcount": 30, "nights": 1, "depart": "강남역"}


# region: retry
async def retry(call, safe, tries=4, wait=0.1):
    """safe — 두 번 해도 결과가 같은 호출(Get·List·Cancel)인가."""
    for n in range(1, tries + 1):
        try:
            return await call()
        except A2AError as e:
            cause = e.__cause__
            # 요청이 떠나지도 못한 실패는 늘 다시 해도 된다.
            # 그 밖의 전송 실패(시간 초과 등)는 safe 일 때만.
            again = isinstance(cause, httpx.ConnectError) or (
                safe and isinstance(cause, httpx.TransportError)
            )
            kind = type(cause if cause else e).__name__
            if not again or n == tries:
                print(f"  시도 {n}: {kind} → 그만")
                raise
            print(f"  시도 {n}: {kind} → {wait}초 뒤 다시")
            await asyncio.sleep(wait)
            wait *= 2  # 지수 백오프(실제로는 지터를 더한다)


# endregion


async def attempt(title, call, safe):
    print(title)
    try:
        await retry(call, safe)
    except A2AError:
        pass


# region: main
async def main(url, dead):
    http = httpx.AsyncClient(timeout=5)
    card = await A2ACardResolver(http, url).get_agent_card()
    live = await create_client(card, ClientConfig(streaming=False))
    get = GetTaskRequest(id="no-such-task")
    await attempt("① 없는 작업", lambda: live.get_task(get), True)
    msg = Message(message_id="m-retry", role=Role.ROLE_USER)
    msg.parts.append(new_data_part(BUS))
    send = SendMessageRequest(message=msg)
    short = ClientCallContext(timeout=1.5)

    async def first():  # 막는 호출의 첫 답(Task)까지
        async for ev in live.send_message(send, context=short):
            return ev

    await attempt("② 1.5초에 끊긴 SendMessage", first, False)
    # 실험용 — 카드의 주소만 아무도 듣지 않는 포트로 바꿔 끼운다
    card.supported_interfaces[0].url = dead
    gone = await create_client(card)
    await attempt(
        "③ 죽은 주소에 GetTask", lambda: gone.get_task(get), True
    )


# endregion

asyncio.run(main(sys.argv[1], sys.argv[2]))
# @ norun
