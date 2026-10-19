"""여러 에이전트의 로그에서 contextId 하나를 따라간다 — grep 의 일.

    python 17/follow.py 첫에이전트 [다른 에이전트…]

첫 에이전트 로그의 첫 줄(바깥에서 들어온 요청)의 ctx 를 열쇠로,
에이전트마다 그 ctx 가 든 줄을 차례로 보인다.
"""

import json
import os
import sys
import tempfile

folder = os.environ.get("A2A_LOG") or os.path.join(
    tempfile.gettempdir(), "a2a-log"
)


def lines(agent):
    with open(
        os.path.join(folder, f"{agent}.jsonl"), encoding="utf-8"
    ) as f:
        return [json.loads(x) for x in f]


# region: follow
agents = sys.argv[1:]
first = lines(agents[0])[0]
raw = json.dumps(first, ensure_ascii=False, separators=(",", ":"))
print("들어온 첫 요청:", raw)
key = first["ctx"]
print(f"따라갈 ctx: {key}\n")
cols = ("agent", "method", "state", "rpc", "task", "took")


def show(row):  # 길이가 바뀌는 값(id·시간)은 뒤로, 두 칸씩 띄워
    a, m, st, *rest = (str(v) for v in row)
    print(f"{a:<11}{m:<21}{st:<15}" + "  ".join(rest))


show(cols)
for a in agents:
    mine = lines(a)
    hit = [r for r in mine if r["ctx"] == key]
    for r in hit:
        st = (r["state"] or "-").removeprefix("TASK_STATE_")
        show((a, r["method"], st, r["rpc"], r["task"], r["took"]))
    if len(hit) < len(mine):
        show((a, f"(다른 ctx 의 줄 {len(mine) - len(hit)}개)", ""))
# endregion
# @ norun
