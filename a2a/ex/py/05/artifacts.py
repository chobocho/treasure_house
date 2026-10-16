# 식사 에이전트에 식단을 맡기고(막는 호출), 끝난 Task 의 아티팩트를
# 하나씩 읽는다 — id·이름·설명, 파트의 종류, metadata·extensions.
#   python 05/artifacts.py 카드주소
import asyncio
import sys

from a2a.client import ClientConfig, create_client
from a2a.helpers.proto_helpers import new_data_part
from a2a.types import Message, Role, SendMessageRequest

MEALS = {"nights": 1, "headcount": 30, "vegetarians": 2}


# region: read
def part(p):
    kind = p.WhichOneof("content")
    if kind == "text":
        return f"text {len(p.text)}자"
    if kind == "raw":
        return f"raw {p.filename} {p.media_type} {len(p.raw)}바이트"
    return f"data {sorted(p.data.struct_value.fields)[:3]}…"


def read(task):
    print("아티팩트", len(task.artifacts), "개")
    for a in task.artifacts:
        print(f"- {a.artifact_id} '{a.name}' 설명:{a.description!r}")
        for p in a.parts:
            print("    ", part(p))
        meta = "있음" if a.HasField("metadata") else "없음"
        print(f"    metadata {meta}, extensions {list(a.extensions)}")


# endregion


async def main(url):
    client = await create_client(url, ClientConfig(streaming=False))
    msg = Message(message_id="meals-1", role=Role.ROLE_USER)
    msg.parts.append(new_data_part(MEALS))
    async for ev in client.send_message(
        SendMessageRequest(message=msg)
    ):
        read(ev.task)
    await client.close()


asyncio.run(main(sys.argv[1]))
# @ norun
