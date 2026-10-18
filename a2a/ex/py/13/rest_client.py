# SDK 클라이언트로 HTTP+JSON 문을 쓴다 — 서버 셋에 같은 세 가지를.
#   python 13/rest_client.py 이름=URL …
# 1) 막는 SendMessage  2) 없는 작업 GetTask  3) 없는 작업에 잇는 스트림
import asyncio
import sys

from a2a.client import ClientConfig, create_client
from a2a.helpers import new_text_part
from a2a.types import (
    GetTaskRequest,
    Message,
    Role,
    SendMessageRequest,
    TaskState,
)


def msg(task_id=""):
    text = new_text_part("2026-10-30 1박 30명")
    return SendMessageRequest(
        message=Message(
            message_id="c-1",
            role=Role.ROLE_USER,
            task_id=task_id,
            parts=[text],
        )
    )


async def kind_of(call):
    try:
        await call()
    except Exception as e:  # noqa: BLE001 — 어떤 예외인지가 답이다
        return type(e).__name__
    return "성공"


# region: client
async def one(label, url):
    # 파이썬 클라이언트는 따로 말하지 않으면 JSON-RPC 만 안다
    config = ClientConfig(supported_protocol_bindings=["HTTP+JSON"])
    stream = await create_client(url, config)
    config = ClientConfig(
        streaming=False, supported_protocol_bindings=["HTTP+JSON"]
    )
    client = await create_client(url, config)
    async for ev in client.send_message(msg()):
        state = TaskState.Name(ev.task.status.state)
    nope = GetTaskRequest(id="t-nope")
    got = await kind_of(lambda: client.get_task(nope))

    async def follow():
        async for _ in stream.send_message(msg("t-nope")):
            pass

    sub = await kind_of(follow)
    print(
        f"{label}: 보내기 {state[11:]} | 없는 작업 {got} | 잇기 {sub}"
    )


# endregion


async def main():
    for arg in sys.argv[1:]:
        await one(*arg.split("=", 1))


asyncio.run(main())
# @ norun
