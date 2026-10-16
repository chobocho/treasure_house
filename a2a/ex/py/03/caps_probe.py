# 카드에 없는 기능 셋을 SDK 클라이언트로 불러 본다. 클라이언트가
# 카드를 먼저 보고 막는지, 서버까지 가서 오류를 받는지 보려는 것.
#   python 03/caps_probe.py 카드주소
import asyncio
import sys

from a2a.client import create_client
from a2a.helpers.proto_helpers import new_text_part
from a2a.types import (
    GetExtendedAgentCardRequest,
    Message,
    Role,
    SendMessageRequest,
    TaskPushNotificationConfig,
)
from a2a.utils.errors import A2AError


def fail(e):
    return f"{type(e).__name__}: {e}"


# region: probe
async def probe(client):
    msg = Message(
        role=Role.ROLE_USER,
        message_id="probe-1",
        parts=[new_text_part("안녕하세요")],
    )
    # send_message 는 카드가 허락하면 스트림, 아니면 막는 호출
    async for ev in client.send_message(
        SendMessageRequest(message=msg)
    ):
        print("① 메시지 →", ev.WhichOneof("payload"))
    hook = TaskPushNotificationConfig(
        task_id="t-1", url="http://127.0.0.1:10399/hook"
    )
    try:
        await client.create_task_push_notification_config(hook)
    except A2AError as e:
        print("② 푸시 설정 →", fail(e))
    try:
        req = GetExtendedAgentCardRequest()
        card = await client.get_extended_agent_card(req)
        print("③ 확장 카드 →", card.name)
    except A2AError as e:
        print("③ 확장 카드 →", fail(e))


# endregion


async def main(url):
    client = await create_client(url)
    await probe(client)
    await client.close()


asyncio.run(main(sys.argv[1]))
# @ norun
