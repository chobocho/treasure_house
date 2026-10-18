# 교통 에이전트에 푸시 설정을 두 번 단다 — 보내는 요청에 하나(inline),
# 돌려받은 작업에 CreateTaskPushNotificationConfig 로 하나. 그다음
# 중계기(relay.py)에 무엇이 왔는지 묻는다.
#   python 11/setup.py 에이전트주소 웹훅주소 중계기주소 [--no-id]
import asyncio
import json
import sys
import urllib.request

from a2a.client import ClientConfig, create_client
from a2a.helpers.proto_helpers import new_data_part
from a2a.types import (
    Message,
    Role,
    SendMessageConfiguration,
    SendMessageRequest,
    TaskPushNotificationConfig,
    TaskState,
)

AGENT, HOOK, RELAY = sys.argv[1:4]
NO_ID = "--no-id" in sys.argv  # Create 에 id 를 주지 않는다
BUS = {"headcount": 30, "nights": 1, "depart": "강남역"}


# region: inline
async def send(client):
    msg = Message(message_id="push-1", role=Role.ROLE_USER)
    msg.parts.append(new_data_part(BUS))
    # 작업 id 는 아직 없으니 task_id 는 비워 둔다(proto 주석)
    push = TaskPushNotificationConfig(url=HOOK, token="tok-inline")
    conf = SendMessageConfiguration(
        return_immediately=True, task_push_notification_config=push
    )
    req = SendMessageRequest(message=msg, configuration=conf)
    async for ev in client.send_message(req):
        return ev.task


# endregion


# region: create
async def create(client, task_id):
    cfg = TaskPushNotificationConfig(
        task_id=task_id, url=HOOK, token="tok-create"
    )
    if not NO_ID:
        cfg.id = "hook-2"  # 설정 id 는 클라이언트가 정할 수 있다
    return await client.create_task_push_notification_config(cfg)


# endregion


def arrivals(task_id):
    """중계기에서 이 작업의 끝 알림을 설정마다 하나씩 기다린다."""
    url = f"{RELAY}wait?task={task_id}&n=2"
    if NO_ID:  # 둘째 설정의 끝 알림만 기다린다(첫째는 덮였을 수 있다)
        url = f"{RELAY}wait?task={task_id}&token=tok-create"
    return json.loads(urllib.request.urlopen(url).read())


async def main():
    client = await create_client(AGENT, ClientConfig(streaming=False))
    task = await send(client)
    state = TaskState.Name(task.status.state)[11:]
    print("SendMessage →", state, task.id)
    got = await create(client, task.id)
    print("Create →", f"id={got.id} taskId={got.task_id}")
    print(f"  url={got.url} token={got.token}")
    # 두 설정으로 가는 알림은 서로 차례가 섞일 수 있어 토큰별로 모은다
    for r in sorted(arrivals(task.id), key=lambda r: r["token"]):
        print(f"  {r['token']:<10} {r['what']}")
    await client.close()


asyncio.run(main())
# @ norun
