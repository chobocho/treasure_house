# 떠 있는 숙소 에이전트를 골든 벡터로 검사한다 — 업무 규칙
# 시험(workshop/test_domain.py)과 같은 기대값을, 이번에는 A2A 를
# 거쳐서. 사례마다 새 작업 하나(막는 호출).
#   python 07/golden_lodging.py URL
import asyncio
import json
import sys
from pathlib import Path

from a2a.client import ClientConfig, create_client
from a2a.helpers import get_data_parts, get_message_text, new_data_part
from a2a.types import Message, Role, SendMessageRequest, TaskState

GOLDEN = Path("../fixtures/golden/domain.json")  # ex/py 에서 돈다


def tidy(d):
    """Value 를 지나 실수가 된 수를 정수로(2장)."""
    return {
        k: int(v) if isinstance(v, float) else v for k, v in d.items()
    }


# region: check
def answer_of(task):
    """완료면 아티팩트의 DataPart, 거절이면 상태 메시지의 까닭."""
    if task.status.state == TaskState.TASK_STATE_COMPLETED:
        return tidy(get_data_parts(task.artifacts[0].parts)[0])
    reason = get_message_text(task.status.message)
    return {"ok": False, "reason": reason}


async def main(url):
    cases = json.loads(GOLDEN.read_text())["chooseLodging"]
    client = await create_client(url, ClientConfig(streaming=False))
    passed = 0
    for i, case in enumerate(cases, 1):
        msg = Message(
            message_id=f"g-{i}",
            role=Role.ROLE_USER,
            parts=[new_data_part(case["input"])],
        )
        async for ev in client.send_message(
            SendMessageRequest(message=msg)
        ):
            got = answer_of(ev.task)
        ok = got == case["expected"]
        passed += ok
        state = TaskState.Name(ev.task.status.state)[11:]
        print(f"{'O' if ok else 'X'} {case['name']:28} {state}")
    print(f"{passed}/{len(cases)} 골든과 같음")
    await client.close()


# endregion

asyncio.run(main(sys.argv[1]))
# @ norun
