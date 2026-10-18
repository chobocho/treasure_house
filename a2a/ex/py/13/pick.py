# 카드에 문이 셋일 때 파이썬 클라이언트는 어느 문을 고르나.
# 설정 셋으로 클라이언트를 지어 같은 메시지를 보낸다. 어느 문으로
# 들어갔는지는 서버(13/doors.py)의 기록이 말한다.
#   python 13/pick.py URL
import asyncio
import sys

import grpc
from a2a.client import ClientConfig, create_client
from a2a.helpers import new_text_part
from a2a.types import Message, Role, SendMessageRequest, TaskState

TWO = ["GRPC", "HTTP+JSON"]  # JSON-RPC 를 뺀 둘, 이 차례로

# region: configs
CONFIGS = {
    "기본": ClientConfig(),
    "GRPC·HTTP+JSON": ClientConfig(supported_protocol_bindings=TWO),
    "GRPC 우선": ClientConfig(
        supported_protocol_bindings=TWO, use_client_preference=True
    ),
}
# endregion


async def main(url):
    text = new_text_part("2026-10-30 1박 30명")
    m = Message(message_id="m-1", role=Role.ROLE_USER, parts=[text])
    for label, config in CONFIGS.items():
        config.streaming = False
        config.grpc_channel_factory = grpc.aio.insecure_channel
        client = await create_client(url, config)
        try:
            req = SendMessageRequest(message=m)
            async for ev in client.send_message(req):
                state = TaskState.Name(ev.task.status.state)[11:]
        except Exception as e:  # noqa: BLE001 — 실패도 한 줄로
            state = f"실패 {type(e).__name__}"
        print(f"{label} → {state}")


asyncio.run(main(sys.argv[1]))
# @ norun
