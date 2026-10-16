# 식사 에이전트에 막는 호출로 식단을 묻고, 아티팩트의 파일 파트를
# 꺼낸다. acceptedOutputModes 에는 "text/markdown 만 받겠다" 고 적는다.
#   python 04/menu_file.py 카드주소
import asyncio
import sys

from a2a.client import ClientConfig, create_client
from a2a.helpers.proto_helpers import new_data_part
from a2a.types import Message, Role, SendMessageRequest

MEALS = {"nights": 1, "headcount": 30, "vegetarians": 2}


# region: file
def show(task):
    for a in task.artifacts:
        kinds = [p.WhichOneof("content") for p in a.parts]
        print(f"{a.name}: {' '.join(kinds)}")
        for p in a.parts:
            if p.WhichOneof("content") != "raw":
                continue
            # p.raw 는 bytes — base64 는 SDK 가 이미 풀었다
            print(f"  {p.filename} {p.media_type} {len(p.raw)}바이트")
            print(p.raw.decode("utf-8"), end="")


# endregion


async def main(url):
    # region: modes
    config = ClientConfig(
        streaming=False, accepted_output_modes=["text/markdown"]
    )
    # endregion
    client = await create_client(url, config)
    msg = Message(
        role=Role.ROLE_USER,
        message_id="menu-py",
        parts=[new_data_part(MEALS)],
    )
    async for ev in client.send_message(
        SendMessageRequest(message=msg)
    ):
        show(ev.task)
    await client.close()


asyncio.run(main(sys.argv[1]))
# @ norun
