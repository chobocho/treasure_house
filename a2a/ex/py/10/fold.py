# SDK 클라이언트로 식사 에이전트의 스트림을 받아 이벤트를 Task 하나로
# 접는다(4장). --cut 이면 첫 조각 뒤에 끊고 SubscribeToTask 로 다시
# 붙어 이어 접는다(5장). 끝으로 GetTask 의 아티팩트와 견준다.
#   python 10/fold.py URL [--cut]
import argparse
import asyncio
from contextlib import aclosing

from a2a.client import ClientConfig, create_client
from a2a.helpers import new_data_part, new_text_part
from a2a.server.tasks.task_manager import append_artifact_to_task
from a2a.types import (
    GetTaskRequest,
    Message,
    Role,
    SendMessageRequest,
    SubscribeToTaskRequest,
    Task,
    TaskState,
)
from a2a.utils.errors import InvalidAgentResponseError

ASK = {"nights": 1, "headcount": 30, "vegetarians": 2}


def name(state):
    return TaskState.Name(state).removeprefix("TASK_STATE_")


def arts(task):
    return " ".join(
        f"{a.artifact_id}×{len(a.parts)}" for a in task.artifacts
    )


# region: fold
def fold(view: Task, ev) -> None:
    """StreamResponse 하나를 view 에 접는다."""
    kind = ev.WhichOneof("payload")
    if kind == "task":  # 첫 이벤트(다시 붙은 뒤에도) — 통째로
        view.CopyFrom(ev.task)
    elif kind == "status_update":  # 상태는 마지막 것이 이긴다
        view.status.CopyFrom(ev.status_update.status)
    elif kind == "artifact_update":
        # SDK 서버가 저장소의 Task 에 쓰는 바로 그 함수
        append_artifact_to_task(view, ev.artifact_update)


# endregion


# region: wrong
def naive(seen: dict, ev) -> None:
    """잘못 접기 — append 를 보지 않고 같은 id 를 덮어쓴다."""
    if ev.HasField("artifact_update"):
        a = ev.artifact_update.artifact
        seen[a.artifact_id] = a


# endregion


# region: files
def files(view: Task) -> None:
    """파일 파트와 데이터 파트를 꺼낸다 — 마지막 두 아티팩트."""
    for a in view.artifacts[1:]:
        p = a.parts[0]
        if p.WhichOneof("content") == "raw":  # 이미 bytes
            head = p.raw.decode().split("\n")[0]
            print(
                f"  {p.filename} {p.media_type} {len(p.raw)}바이트",
                end="",
            )
            print(f" — {head!r}")
        elif p.WhichOneof("content") == "data":  # Value → Struct
            total = p.data.struct_value["total"]
            print(
                f"  {a.name} total {total!r} ({type(total).__name__})"
            )


# endregion


# region: send
async def main(url, cut):
    client = await create_client(url, ClientConfig(streaming=True))
    parts = [new_text_part("식단 부탁합니다"), new_data_part(ASK)]
    msg = Message(message_id="f-1", role=Role.ROLE_USER, parts=parts)
    view, wrong, n = Task(), {}, 0
    req = SendMessageRequest(message=msg)
    async with aclosing(client.send_message(req)) as stream:
        async for ev in stream:
            fold(view, ev)
            naive(wrong, ev)
            n += 1
            if cut and ev.HasField("artifact_update"):
                print(f"이벤트 {n}개 뒤에 끊음 — {arts(view)}")
                break  # aclosing 이 응답을 닫는다
    if cut:
        await resubscribe(client, view, wrong)
    else:
        print(f"이벤트 {n}개")
    print(f"접은 Task — {name(view.status.state)} {arts(view)}")
    for p in view.artifacts[0].parts:
        print("  " + p.text, end="")
    files(view)
    got = await client.get_task(GetTaskRequest(id=view.id))
    same = list(got.artifacts) == list(view.artifacts)
    print(f"GetTask 와 아티팩트가 같다: {same}")
    plan = wrong["meal-plan"]
    print(f"덮어쓰기만 하면 meal-plan×{len(plan.parts)}:", end=" ")
    print(plan.parts[0].text, end="")
    await client.close()


# endregion


# region: resub
async def resubscribe(client, view, wrong):
    """같은 taskId 로 다시 붙어 이어 접는다. 첫 이벤트는 Task."""
    req = SubscribeToTaskRequest(id=view.id)
    m, bare = 0, Task(id=view.id, context_id=view.context_id)
    async for ev in client.subscribe(req):
        m += 1
        if m == 1:
            t = ev.task
            print(f"다시 붙음 — task {name(t.status.state)} {arts(t)}")
        elif ev.HasField("artifact_update") and bare is not None:
            try:  # 첫 Task 를 버리고 빈 Task 에 접으면?
                append_artifact_to_task(bare, ev.artifact_update)
            except InvalidAgentResponseError as e:
                print(f"  첫 Task 없이 접으면: {type(e).__name__}")
                bare = None
        fold(view, ev)
        naive(wrong, ev)
    print(f"구독으로 이벤트 {m}개")


# endregion

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("url")
    p.add_argument("--cut", action="store_true")
    args = p.parse_args()
    asyncio.run(main(args.url, args.cut))
# @ norun
