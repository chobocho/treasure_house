# 모르는 필드가 든 답을 파이썬 SDK 클라이언트는 어떻게 읽나.
#   python 07/strict.py URL
import asyncio
import sys

from a2a.client import A2AClientError, ClientConfig, create_client
from a2a.helpers import new_text_message
from a2a.types import Role, SendMessageRequest, TaskState
from google.protobuf.json_format import ParseError

NAMES = ["plain", "task", "status", "result", "envelope", "enum"]


def first_line(e):
    return str(e).splitlines()[0]


# region: probe
async def probe(url, streaming):
    config = ClientConfig(streaming=streaming)
    client = await create_client(url, config)  # 카드에도 모르는 필드
    print("스트림" if streaming else "막는 호출")
    for name in NAMES:
        msg = new_text_message(name, role=Role.ROLE_USER)
        try:
            async for ev in client.send_message(
                SendMessageRequest(message=msg)
            ):
                state = TaskState.Name(ev.task.status.state)
                print(f"  {name:9} 받음 {state}")
        except (A2AClientError, ParseError) as e:
            print(f"  {name:9} {type(e).__name__}: {first_line(e)}")
    await client.close()


# endregion


async def main(url):
    await probe(url, streaming=False)
    await probe(url, streaming=True)
    sub = issubclass(ParseError, A2AClientError)
    print("ParseError 는 A2AClientError 인가:", sub)


asyncio.run(main(sys.argv[1]))
# @ norun
