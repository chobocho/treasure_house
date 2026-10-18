# 정산 에이전트에 남은 작업을 상태별로 센다 — 결재를 기다리다 버려진
# 작업(AUTH_REQUIRED)이 있는지 본다. 기획 에이전트와 같은 클라이언트
# (planner)의 토큰으로 묻는다 — 작업의 주인이 같아야 목록에 든다.
#   python 15/settle_left.py 정산URL
import asyncio
import sys

import httpx
from a2a.client import ClientConfig, create_client
from a2a.types import ListTasksRequest, TaskState

STATES = ("AUTH_REQUIRED", "CANCELED", "REJECTED", "COMPLETED")


async def main(url):
    form = {
        "grant_type": "client_credentials",
        "client_id": "planner",
        "client_secret": "planner-secret",
        "scope": "payment:read",
    }
    async with httpx.AsyncClient() as http:
        r = await http.post(url + "oauth/token", data=form)
    token = r.json()["access_token"]
    http = httpx.AsyncClient(
        headers={"Authorization": f"Bearer {token}"}, timeout=30
    )
    config = ClientConfig(streaming=False, httpx_client=http)
    client = await create_client(url, config)
    for name in STATES:
        state = TaskState.Value(f"TASK_STATE_{name}")
        page = await client.list_tasks(ListTasksRequest(status=state))
        print(f"{name:<13} {len(page.tasks)}")
    await client.close()


asyncio.run(main(sys.argv[1]))
# @ norun
