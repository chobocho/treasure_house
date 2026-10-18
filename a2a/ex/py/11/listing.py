# ListTasks — 작업 셋(맥락 ctx-a 에 30명·0명, ctx-b 에 70명)을 만든 뒤
# 필터·페이지·이력 길이를 바꿔 가며 목록을 받는다.
#   python 11/listing.py 에이전트
import asyncio
import sys

from a2a.client import ClientConfig, create_client
from a2a.helpers.proto_helpers import new_data_part
from a2a.types import (
    ListTasksRequest,
    Message,
    Role,
    SendMessageRequest,
    TaskState,
)

JOBS = [  # (messageId, contextId, 요청)
    ("list-a", "ctx-a", {"headcount": 30, "nights": 1}),
    ("list-b", "ctx-a", {"headcount": 0, "nights": 1}),
    ("list-c", "ctx-b", {"headcount": 70, "nights": 2}),
]


async def make(client):
    for mid, ctx, data in JOBS:  # 막는 호출 — 끝나야 다음으로
        msg = Message(
            message_id=mid, context_id=ctx, role=Role.ROLE_USER
        )
        msg.parts.append(new_data_part(data))
        async for _ in client.send_message(
            SendMessageRequest(message=msg)
        ):
            pass


def row(t):
    """작업 하나 → 맥락·상태·첫 메시지·이력 수·아티팩트 수."""
    first = t.history[0].message_id if t.history else "-"
    state = TaskState.Name(t.status.state)[11:]
    return (
        f"{t.context_id} {state:<9} {first:<6}"
        f" 이력 {len(t.history)} 아티팩트 {len(t.artifacts)}"
    )


# region: list
async def show(client, title, **kw):
    res = await client.list_tasks(ListTasksRequest(**kw))
    more = "있음" if res.next_page_token else '""'
    print(
        f"{title}: total {res.total_size} page {res.page_size}", end=""
    )
    print(f" next {more}")
    for t in res.tasks:
        print("  ", row(t))
    return res.next_page_token


async def lists(client):
    await show(client, "전부")
    await show(client, "contextId=ctx-a", context_id="ctx-a")
    done = TaskState.TASK_STATE_COMPLETED
    await show(client, "status=COMPLETED", status=done)
    token, n = "", 1
    while True:  # 한 장에 하나씩 — 토큰이 빌 때까지
        token = await show(
            client, f"pageSize=1 ({n})", page_size=1, page_token=token
        )
        if not token:
            break
        n += 1
    await show(
        client,
        "historyLength=0 + 아티팩트",
        history_length=0,
        include_artifacts=True,
    )


# endregion


async def main():
    client = await create_client(
        sys.argv[1], ClientConfig(streaming=False)
    )
    await make(client)
    await lists(client)
    await client.close()


asyncio.run(main())
# @ norun
