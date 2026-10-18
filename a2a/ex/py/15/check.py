# 대조기 — 기획 에이전트의 끝난 작업에서 계획서를 꺼내 골든 숫자와
# 맞춘다(SCENARIO §2.6). 이야기를 다시 돌리지 않고 ListTasks 로 읽는다.
#   python 15/check.py 기획에이전트URL
import asyncio
import json
import sys
from pathlib import Path

from a2a.client import create_client
from a2a.helpers import get_data_parts
from a2a.types import ListTasksRequest, TaskState

GOLDEN = Path(__file__).resolve().parents[2] / "fixtures/golden"


# region: golden
def story(fn, name="story"):
    """골든 파일에서 이야기 한 문장의 기댓값을 꺼낸다."""
    cases = json.loads((GOLDEN / "domain.json").read_text())[fn]
    return next(c for c in cases if c["name"] == name)["expected"]


def won(n):
    return f"{n:,}원"


lodging, meals = story("chooseLodging"), story("planMeals")
bus, sheet = story("chooseBuses"), story("settle", "story-approved")
# 계획서 마크다운의 줄 머리 → 그 줄에 있어야 할 글
LINES = {
    "- 숙소:": [lodging["venueName"], f"{lodging['rooms']}실"]
    + [won(lodging["total"])],
    "- 식사:": [f"{len(meals['slots'])}끼", won(meals["total"])],
    "- 교통:": [f"{bus['days']}일", won(bus["total"])],
    "- 합계:": [
        won(sheet[k]) for k in ("total", "budget", "remaining")
    ],
}
# 요약 DataPart = 풀이 결과 + 합계
SUMMARY = {**story("parseRequest"), "total": sheet["total"]}
# endregion


# region: check
async def main(url):
    client = await create_client(url)
    page = await client.list_tasks(
        ListTasksRequest(
            status=TaskState.TASK_STATE_COMPLETED,
            include_artifacts=True,
        )
    )
    [task] = page.tasks  # 이 기획 에이전트가 끝낸 작업은 하나뿐
    [plan] = [a for a in task.artifacts if a.name == "워크숍 계획서"]
    md, summary = plan.parts  # 마크다운 TextPart, 요약 DataPart
    print(
        "✓" if md.media_type == "text/markdown" else "✗", md.media_type
    )
    bad = 0
    for head, words in LINES.items():
        line = next(
            x for x in md.text.splitlines() if x.startswith(head)
        )
        ok = all(w in line for w in words)
        bad += not ok
        print("✓" if ok else "✗", head, " · ".join(words))
    data = get_data_parts([summary])[0]
    # 30.0 == 30 — 파이썬이 보낸 실수도 수의 값으로 견준다
    miss = [k for k, want in SUMMARY.items() if data.get(k) != want]
    for k in miss:
        print("✗ 요약", k, data.get(k), "≠", SUMMARY[k])
    n, bad = len(SUMMARY), bad + len(miss)
    print(
        "✓" if not miss else "✗", f"요약 DataPart {n - len(miss)}/{n}"
    )
    await client.close()
    sys.exit(1 if bad else 0)


asyncio.run(main(sys.argv[1]))
# endregion
# @ norun
