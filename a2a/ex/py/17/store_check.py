# 파일 저장소 실험의 클라이언트 — 하위 명령 넷.
#   python 17/store_check.py make|start|look|poke 카드주소
#   make  막는 호출로 작업 하나를 끝내고, 푸시 설정을 하나 단다
#   start returnImmediately 로 맡기고 첫 단계(WORKING)에서 나온다
#   look  ListTasks 로 저장된 작업과 그 푸시 설정 수를 본다
#   poke  WORKING 작업에 구독(2초)과 CancelTask 를 해 본다
import asyncio
import sys

from a2a.client import ClientConfig, create_client
from a2a.helpers.proto_helpers import new_data_part
from a2a.types import (
    CancelTaskRequest,
    GetTaskRequest,
    ListTaskPushNotificationConfigsRequest,
    ListTasksRequest,
    Message,
    Role,
    SendMessageConfiguration,
    SendMessageRequest,
    SubscribeToTaskRequest,
    TaskPushNotificationConfig,
    TaskState,
)
from a2a.utils.errors import A2AError

BUS = {"headcount": 30, "nights": 1, "depart": "강남역"}
WORKING = TaskState.TASK_STATE_WORKING


def name(state):
    return TaskState.Name(state).removeprefix("TASK_STATE_")


def said(task):
    return " ".join(p.text for p in task.status.message.parts)


def ask(mid, now):
    msg = Message(message_id=mid, role=Role.ROLE_USER)
    msg.parts.append(new_data_part(BUS))
    conf = SendMessageConfiguration(return_immediately=now)
    return SendMessageRequest(message=msg, configuration=conf)


async def make(c):
    async for ev in c.send_message(ask("m-keep", False)):
        t = ev.task
    arts = [a.name for a in t.artifacts]
    print("make  →", t.id, name(t.status.state), arts)
    cfg = TaskPushNotificationConfig(
        task_id=t.id, id="hook-1", url="http://127.0.0.1:11799/hook"
    )
    await c.create_task_push_notification_config(cfg)
    print("        푸시 설정 hook-1 을 달았다")


async def start(c):
    async for ev in c.send_message(ask("m-cut", True)):
        t = ev.task
    while t.status.state != WORKING:  # 첫 단계가 시작될 때까지
        await asyncio.sleep(0.05)
        t = await c.get_task(GetTaskRequest(id=t.id))
    print("start →", t.id, name(t.status.state), said(t))


# region: look
async def look(c):
    page = await c.list_tasks(ListTasksRequest(include_artifacts=True))
    print(f"look  → 작업 {len(page.tasks)}건")
    for t in sorted(page.tasks, key=lambda t: t.history[0].message_id):
        req = ListTaskPushNotificationConfigsRequest(task_id=t.id)
        hooks = await c.list_task_push_notification_configs(req)
        arts = [a.name for a in t.artifacts]
        print(
            f"   {t.id} {t.history[0].message_id}", name(t.status.state)
        )
        print(
            f"      {said(t)!r} {arts} 푸시 설정 {len(hooks.configs)}개"
        )


# endregion


# region: poke
async def poke(c):
    req = ListTasksRequest(status=WORKING)
    t = (await c.list_tasks(req)).tasks[0]
    sub = c.subscribe(SubscribeToTaskRequest(id=t.id))
    try:
        while True:  # 2초 동안 아무것도 오지 않으면 그만 듣는다
            ev = await asyncio.wait_for(anext(sub), 2)
            print("poke  → 구독", ev.WhichOneof("payload"))
    except TimeoutError:
        print("        2초 동안 더 오지 않음")
    except StopAsyncIteration:
        print("        스트림이 닫힘")
    try:
        t = await c.cancel_task(CancelTaskRequest(id=t.id))
        print("        CancelTask →", name(t.status.state), said(t))
    except A2AError as e:
        print("        CancelTask →", type(e).__name__, e)


# endregion


async def main(cmd, url):
    c = await create_client(url, ClientConfig(streaming=cmd == "poke"))
    await {"make": make, "start": start, "look": look, "poke": poke}[
        cmd
    ](c)


asyncio.run(main(*sys.argv[1:]))
# @ norun
