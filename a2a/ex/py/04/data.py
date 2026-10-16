# 숙소 요청 {date, nights, headcount} 를 DataPart 로 보낸다.
# 답이 Message 면 글을, Task 면 상태와 견적의 수 셋을 찍는다.
#   python 04/data.py 카드주소
import asyncio
import sys

from a2a.client import ClientConfig, create_client
from a2a.helpers.proto_helpers import get_data_parts, new_data_part
from a2a.types import Message, Role, SendMessageRequest, TaskState

# region: send
REQUEST = {"date": "2026-10-30", "nights": 1, "headcount": 30}


def lodging_message():
    # dict → google.protobuf.Value(ParseDict). 수는 모두 double 이 된다
    part = new_data_part(REQUEST)
    return Message(
        message_id="data-py", role=Role.ROLE_USER, parts=[part]
    )


# endregion


# region: read
def show_quote(task):
    print("task", TaskState.Name(task.status.state))
    quote = get_data_parts(task.artifacts[0].parts)[0]  # → dict
    for k in ("headcount", "rooms", "total"):
        v = quote[k]
        print(f"  {k}: {type(v).__name__} {v!r}")


# endregion


async def main(url):
    # 카드가 스트림을 허락해도 막는 호출로 — 끝난 Task 하나만 받는다
    config = ClientConfig(streaming=False)
    client = await create_client(url, config)
    req = SendMessageRequest(message=lodging_message())
    async for ev in client.send_message(req):
        # region: dispatch
        # StreamResponse 의 oneof payload — task 인가 message 인가
        if ev.WhichOneof("payload") == "task":
            show_quote(ev.task)
        else:
            for p in ev.message.parts:
                print(p.text)
        # endregion
    await client.close()


asyncio.run(main(sys.argv[1]))
# @ norun
