# contextId·taskId 규칙(§3.4)을 접수 에이전트에 차례로 두드려 본다.
# 여섯 번 보내고, 답의 상태·작업 id·맥락 id 나 오류를 한 줄씩 찍는다.
#   python 04/ctx_rules.py 카드주소
import asyncio
import itertools
import sys

from a2a.client import ClientConfig, create_client
from a2a.helpers.proto_helpers import new_text_part
from a2a.types import Message, Role, SendMessageRequest, TaskState
from a2a.utils.errors import A2AError

N = itertools.count(1)  # messageId 가 겹치지 않게


# region: send
async def send(client, label, text, task_id="", context_id=""):
    msg = Message(
        role=Role.ROLE_USER,
        message_id=f"ctx-py-{next(N)}",
        parts=[new_text_part(text)],
        task_id=task_id,  # "" 이면 와이어에 나가지 않는다
        context_id=context_id,
    )
    try:
        async for ev in client.send_message(
            SendMessageRequest(message=msg)
        ):
            t = ev.task
            st = TaskState.Name(t.status.state).removeprefix(
                "TASK_STATE_"
            )
            print(f"{label} {st} task={t.id} ctx={t.context_id}")
            return t
    except A2AError as e:
        print(f"{label} {type(e).__name__}: {e}")


# endregion


async def main(url):
    c = await create_client(url, ClientConfig(streaming=False))
    # region: rules
    t1 = await send(c, "①", "워크숍 접수")
    await send(c, "②", "20명", context_id=t1.context_id)
    await send(c, "③", "30명", t1.id, "ctx-다른-맥락")
    await send(c, "④", "30명", task_id=t1.id)
    await send(c, "⑤", "30명", task_id="t-없는-작업")
    await send(c, "⑥", "25명", context_id="ctx-워크숍")
    # endregion
    await c.close()


asyncio.run(main(sys.argv[1]))
# @ norun
