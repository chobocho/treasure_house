# 클라이언트 쪽에서 오류는 어떤 예외로 오나.
#   python 07/client_errors.py URL DEAD_URL
# URL 은 숙소 에이전트, DEAD_URL 은 아무도 듣지 않는 주소다.
import asyncio
import sys

import httpx
from a2a.client import A2ACardResolver, A2AClientError, create_client
from a2a.helpers import new_text_message
from a2a.types import (
    AgentCard,
    GetTaskRequest,
    Role,
    SendMessageRequest,
)
from a2a.utils.errors import A2AError


def report(label, e):
    kind = "A2AClientError" if isinstance(e, A2AClientError) else ""
    kind = kind or ("A2AError" if isinstance(e, A2AError) else "?")
    print(f"{label}: {type(e).__name__} ({kind} 갈래)")
    line = str(e).splitlines()[0]
    print("   ", line[:180] + ("…" if len(line) > 180 else ""))


# region: errors
async def main(url, dead):
    try:  # ① 카드를 받을 수 없다
        await create_client(dead)
    except A2AError as e:
        report("① 닿지 않는 카드", e)
    try:  # ② 카드 경로가 404
        await create_client(url + "nothing/")
    except A2AError as e:
        report("② 없는 카드", e)
        print("    status_code =", e.status_code)
    async with httpx.AsyncClient() as http:  # 카드만 따로 받기
        card = await A2ACardResolver(http, url).get_agent_card()
    client = await create_client(card)
    try:  # ③ 서버가 JSON-RPC 오류로 답했다
        await client.get_task(GetTaskRequest(id="t-없음"))
    except A2AError as e:
        report("③ 없는 작업", e)
    bad = AgentCard()  # 인터페이스 url 만 틀리게 고친 사본
    bad.CopyFrom(card)
    bad.supported_interfaces[0].url = url + "rpc"
    wrong = await create_client(bad)
    msg = new_text_message("숙소", role=Role.ROLE_USER)
    try:  # ④ JSON-RPC 경로가 없다 — HTTP 404
        async for _ in wrong.send_message(
            SendMessageRequest(message=msg)
        ):
            pass
    except A2AError as e:
        report("④ 틀린 url", e)
    await client.close()
    await wrong.close()


# endregion

asyncio.run(main(sys.argv[1], sys.argv[2]))
# @ norun
