# 스트림에 시간 제한 1.5초 — 파이썬(httpx)의 제한은 "읽기 한 번" 이다.
#   python 17/stream_to.py 카드주소
import asyncio
import sys

import httpx
from a2a.client import ClientConfig, create_client
from a2a.client.errors import A2AClientTimeoutError
from a2a.helpers.proto_helpers import new_data_part
from a2a.types import (
    GetTaskRequest,
    Message,
    Role,
    SendMessageRequest,
    TaskState,
)

BUS = {"headcount": 30, "nights": 1, "depart": "강남역"}


def name(state):
    return TaskState.Name(state).removeprefix("TASK_STATE_")


def show(ev):
    kind = ev.WhichOneof("payload")
    if kind == "task":
        return f"Task {name(ev.task.status.state)}"
    if kind == "status_update":
        st = ev.status_update.status
        said = [p.text for p in st.message.parts]  # 끝 상태엔 말이 없다
        return " ".join(["상태", name(st.state), *said])
    return f"아티팩트 {ev.artifact_update.artifact.name}"


# region: main
async def main(url):
    # region: limit
    http = httpx.AsyncClient(timeout=1.5)  # 클라이언트 전체의 제한
    client = await create_client(url, ClientConfig(httpx_client=http))
    # endregion
    msg = Message(message_id="m-stream", role=Role.ROLE_USER)
    msg.parts.append(new_data_part(BUS))
    task_id = ""
    try:
        async for ev in client.send_message(
            SendMessageRequest(message=msg)
        ):
            print("  ", show(ev))
            task_id = task_id or ev.task.id  # 첫 이벤트가 Task
        print("스트림 끝")
    except A2AClientTimeoutError as e:
        print("시간 초과 →", type(e).__name__)
    await asyncio.sleep(3)  # 서버의 세 단계가 다 지나도록
    task = await client.get_task(GetTaskRequest(id=task_id))
    print("3초 뒤 GetTask →", name(task.status.state))


# endregion

asyncio.run(main(sys.argv[1]))
# @ norun
