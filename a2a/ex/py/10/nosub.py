# 스트리밍을 켜지 않은 카드(3부의 안내 에이전트)에 SDK 클라이언트로
# 스트림 보내기와 SubscribeToTask 를 부른다 — 무엇이 서버까지 가나.
#   python 10/nosub.py URL
import asyncio
import sys

from a2a.client import ClientConfig, create_client
from a2a.helpers import new_text_part
from a2a.types import (
    Message,
    Role,
    SendMessageRequest,
    SubscribeToTaskRequest,
)
from a2a.utils.errors import A2AError


# region: probe
async def main(url):
    client = await create_client(url, ClientConfig(streaming=True))
    parts = [new_text_part("안녕하세요")]
    msg = Message(message_id="n-1", role=Role.ROLE_USER, parts=parts)
    async for ev in client.send_message(
        SendMessageRequest(message=msg)
    ):
        print("① 스트림 보내기 →", ev.WhichOneof("payload"))
    try:
        req = SubscribeToTaskRequest(id="t-1")
        async for ev in client.subscribe(req):
            print("② 구독 →", ev.WhichOneof("payload"))
    except (NotImplementedError, A2AError) as e:
        print(f"② 구독 → {type(e).__name__}: {e}")
    await client.close()


# endregion

asyncio.run(main(sys.argv[1]))
# @ norun
