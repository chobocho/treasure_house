# 클라이언트의 갈고리 둘 — 우리 httpx 클라이언트와 가로채기.
# 상대는 머리글을 되돌려 주는 실험 서버(07/headers.py)다. 그 서버엔
# 카드 경로가 없어 카드를 손에 쥔 채로 클라이언트를 만든다.
#   python 07/client_hooks.py URL
import asyncio
import sys

import httpx
from a2a.client import (
    ClientCallContext,
    ClientCallInterceptor,
    ClientConfig,
    create_client,
)
from a2a.helpers import get_message_text, new_text_message
from a2a.types import Role, SendMessageRequest
from step1_echo import card


# region: interceptor
class TeamHeader(ClientCallInterceptor):
    """보내기 전에 머리글을 하나 달고, 받은 뒤 답의 타입을 찍는다."""

    async def before(self, args):
        print(f"  before {args.method}")
        ctx = args.context or ClientCallContext()
        params = dict(ctx.service_parameters or {})
        params["X-Workshop-Team"] = "general-affairs"
        ctx.service_parameters = params  # 이것이 HTTP 머리글이 된다
        args.context = ctx

    async def after(self, args):
        print(f"  after  {args.method} → {type(args.result).__name__}")


# endregion


# region: main
async def main(url):
    http = httpx.AsyncClient(timeout=10)  # 연결은 우리 것
    print("만들기 전 A2A-Version:", http.headers.get("A2A-Version"))
    config = ClientConfig(streaming=False, httpx_client=http)
    client = await create_client(
        card(url), config, interceptors=[TeamHeader()]
    )
    print("만든 뒤 A2A-Version:", http.headers.get("A2A-Version"))
    msg = new_text_message("누구세요", role=Role.ROLE_USER)
    async for ev in client.send_message(
        SendMessageRequest(message=msg)
    ):
        print(" ", get_message_text(ev.message, delimiter=" | "))
    await client.close()
    print("닫힌 뒤 httpx:", http.is_closed)


# endregion

asyncio.run(main(sys.argv[1]))
# @ norun
