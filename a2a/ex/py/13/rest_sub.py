# SDK 클라이언트의 SubscribeToTask 는 HTTP+JSON 에서 어떤 동사로 가나.
# 없는 작업에 잇기만 한 번 — 동사는 탭이 본다(5장).
#   python 13/rest_sub.py URL
import asyncio
import sys

from a2a.client import ClientConfig, create_client
from a2a.types import SubscribeToTaskRequest


# region: sub
async def main(url):
    config = ClientConfig(supported_protocol_bindings=["HTTP+JSON"])
    client = await create_client(url, config)
    try:
        req = SubscribeToTaskRequest(id="t-nope")
        async for _ in client.subscribe(req):
            pass
    except Exception as e:  # noqa: BLE001 — 어떤 예외인지가 답이다
        print("잇기:", type(e).__name__)


# endregion
asyncio.run(main(sys.argv[1]))
# @ norun
