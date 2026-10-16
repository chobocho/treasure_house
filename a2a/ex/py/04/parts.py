# 파트 네 가지(text·raw·url·data)를 한 메시지에 담아 보낸다.
#   python 04/parts.py 카드주소
import asyncio
import sys

from a2a.client import create_client
from a2a.helpers.proto_helpers import (
    new_data_part,
    new_raw_part,
    new_url_part,
)
from a2a.types import Message, Part, Role, SendMessageRequest

MENU = "# 식단\n- 숯불 바비큐\n".encode()  # str → UTF-8 바이트


# region: parts
def four_parts():
    return [
        # 생성자에 oneof 의 필드 하나를 이름으로 준다
        Part(text="워크숍 자료 넷을 보냅니다"),
        # 도우미는 같은 필드를 채워 줄 뿐이다
        new_raw_part(MENU, "text/markdown", "menu.md"),
        new_url_part(
            "https://treasure-house.example/map.png",
            "image/png",
            "map.png",
        ),
        new_data_part(["숙소", "식사", "교통"]),
    ]


# endregion


async def main(url):
    client = await create_client(url)
    msg = Message(
        message_id="parts-py", role=Role.ROLE_USER, parts=four_parts()
    )
    async for ev in client.send_message(
        SendMessageRequest(message=msg)
    ):
        print("답:", ev.WhichOneof("payload"))
        for p in ev.message.parts:
            print(p.text)
    await client.close()


asyncio.run(main(sys.argv[1]))
# @ norun
