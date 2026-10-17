# SDK 클라이언트로 숙소 견적을 묻는다 — 막는 호출과 스트림.
#   python 07/client_send.py URL [--no-stream]
import argparse
import asyncio

from a2a.client import ClientConfig, create_client
from a2a.helpers import new_data_part
from a2a.types import (
    GetTaskRequest,
    Message,
    Role,
    SendMessageRequest,
    TaskState,
)


def name(state):
    return TaskState.Name(state).removeprefix("TASK_STATE_")


# region: show
def show(ev):
    """StreamResponse 하나 — 넷 중 무엇이 들었는지는 oneof 로."""
    kind = ev.WhichOneof("payload")
    if kind == "task":
        t = ev.task
        print(
            f"  task {name(t.status.state)} 아티팩트 {len(t.artifacts)}"
        )
    elif kind == "status_update":
        print(f"  status_update {name(ev.status_update.status.state)}")
    elif kind == "artifact_update":
        print(f"  artifact_update {ev.artifact_update.artifact.name}")
    else:
        print("  message")


# endregion


# region: send
async def main(url, streaming):
    config = ClientConfig(streaming=streaming)
    client = await create_client(url, config)  # 카드부터 읽는다
    req = {"date": "2026-10-30", "nights": 1, "headcount": 30}
    msg = Message(
        message_id="c-1",
        role=Role.ROLE_USER,
        parts=[new_data_part(req)],
    )
    print("스트림" if streaming else "막는 호출")
    task_id = None
    async for ev in client.send_message(
        SendMessageRequest(message=msg)
    ):
        show(ev)
        task_id = task_id or ev.task.id or ev.status_update.task_id
    task = await client.get_task(GetTaskRequest(id=task_id))
    print(f"GetTask: {name(task.status.state)}", end=" ")
    print(f"아티팩트 {len(task.artifacts)} 이력 {len(task.history)}")
    await client.close()


# endregion

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("url")
    p.add_argument("--no-stream", action="store_true")
    args = p.parse_args()
    asyncio.run(main(args.url, not args.no_stream))
# @ norun
