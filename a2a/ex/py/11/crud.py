# 푸시 설정 CRUD — 설정 둘(요청에 실은 hook-1, Create 한 hook-2)을 단
# 작업에 Get·List·Delete 를 차례로 한다. 지운 설정으로는 알림이 더 가지
# 않는지 중계기(relay.py)에서 본다. 마지막은 없는 설정을 Get.
#   python 11/crud.py 에이전트 웹훅 중계기 [--no-id]
# --no-id 면 두 설정 모두 id 없이 달고 List 만 한다.
import asyncio
import json
import sys
import urllib.request

from a2a.client import ClientConfig, create_client
from a2a.helpers.proto_helpers import new_data_part
from a2a.types import (
    DeleteTaskPushNotificationConfigRequest,
    GetTaskPushNotificationConfigRequest,
    ListTaskPushNotificationConfigsRequest,
    Message,
    Role,
    SendMessageConfiguration,
    SendMessageRequest,
    TaskPushNotificationConfig,
)
from a2a.utils.errors import A2AError

AGENT, HOOK, RELAY = sys.argv[1:4]
NO_ID = "--no-id" in sys.argv
BUS = {"headcount": 30, "nights": 1, "depart": "강남역"}


def cfg(cid, token, task_id=""):
    c = TaskPushNotificationConfig(
        task_id=task_id, url=HOOK, token=token
    )
    if not NO_ID:
        c.id = cid
    return c


async def setup(client):
    msg = Message(message_id="crud-1", role=Role.ROLE_USER)
    msg.parts.append(new_data_part(BUS))
    conf = SendMessageConfiguration(
        return_immediately=True,
        task_push_notification_config=cfg("hook-1", "tok-1"),
    )
    req = SendMessageRequest(message=msg, configuration=conf)
    async for ev in client.send_message(req):
        task = ev.task
    await client.create_task_push_notification_config(
        cfg("hook-2", "tok-2", task.id)
    )
    return task.id


# region: list
async def show(client, tid):
    res = await client.list_task_push_notification_configs(
        ListTaskPushNotificationConfigsRequest(task_id=tid)
    )
    # 서버가 돌려주는 차례는 정해져 있지 않다 — 토큰으로 줄 세운다
    got = sorted(res.configs, key=lambda c: c.token)
    print(f"List → {len(got)}개", [f"{c.id}:{c.token}" for c in got])


# endregion


# region: crud
async def crud(client, tid):
    get = GetTaskPushNotificationConfigRequest(task_id=tid, id="hook-2")
    c = await client.get_task_push_notification_config(get)
    print(f"Get hook-2 → url={c.url} token={c.token}")
    await show(client, tid)
    gone = DeleteTaskPushNotificationConfigRequest(
        task_id=tid, id="hook-1"
    )
    for n in (1, 2):  # 두 번 지운다 — 명세는 멱등(idempotent)
        try:
            await client.delete_task_push_notification_config(gone)
            print(f"Delete hook-1 ({n}) → 오류 없음")
        except A2AError as e:
            print(f"Delete hook-1 ({n}) → {type(e).__name__}: {e}")
    await show(client, tid)
    try:  # 지운 설정을 다시 Get
        get.id = "hook-1"
        await client.get_task_push_notification_config(get)
    except A2AError as e:
        print(f"Get hook-1 → {type(e).__name__}: {e}")


# endregion


def arrivals(tid):
    """tok-2 의 끝 알림을 기다린 뒤, 토큰마다 받은 것을 센다."""
    url = f"{RELAY}wait?task={tid}&token=tok-2"
    seen = {}
    for r in json.loads(urllib.request.urlopen(url).read()):
        seen.setdefault(r["token"], []).append(r["what"])
    for token in sorted(seen):
        print(f"  {token} {len(seen[token])}건 — 첫 {seen[token][0]}")


async def main():
    client = await create_client(AGENT, ClientConfig(streaming=False))
    tid = await setup(client)
    print("작업", tid)
    if NO_ID:
        await show(client, tid)
    else:
        await crud(client, tid)
    arrivals(tid)
    await client.close()


asyncio.run(main())
# @ norun
