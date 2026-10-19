# SDK 기본값 그대로 — 6초 걸리는 배차를 막는 호출로 맡긴다.
#   python 17/defaults.py 카드주소
import asyncio
import sys

from a2a.client import ClientConfig, create_client
from a2a.client.errors import A2AClientError
from a2a.helpers.proto_helpers import new_data_part
from a2a.types import Message, Role, SendMessageRequest, TaskState

BUS = {"headcount": 30, "nights": 1, "depart": "강남역"}


# region: main
async def main(url):
    # region: make
    # httpx_client 를 주지 않으면 SDK 가 httpx.AsyncClient() 를 짓는다
    client = await create_client(url, ClientConfig(streaming=False))
    # endregion
    msg = Message(message_id="m-default", role=Role.ROLE_USER)
    msg.parts.append(new_data_part(BUS))
    try:
        async for ev in client.send_message(
            SendMessageRequest(message=msg)
        ):
            state = TaskState.Name(ev.task.status.state)
            print("SendMessage →", state)
    except A2AClientError as e:  # 클라이언트 쪽 오류의 뿌리
        print("SendMessage →", type(e).__name__, e)
        print("  원인:", type(e.__cause__).__name__)


# endregion

asyncio.run(main(sys.argv[1]))
# @ norun
