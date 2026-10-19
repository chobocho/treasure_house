# TCK 의 실패 셋을 맨손으로 다시 본다 — 카드의 캐시 머리글, 빈
# ListTasks 의 tasks, SendMessage 의 historyLength 0.
#   python 16/tck_why.py LABEL PORT
import json
import sys

import httpx

label, port = sys.argv[1], sys.argv[2]
url = f"http://127.0.0.1:{port}/"
http = httpx.Client(headers={"A2A-Version": "1.0"})


def rpc(method, params):
    body = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params,
    }
    return http.post(url, json=body).json()["result"]


# region: card
card = http.get(url + ".well-known/agent-card.json")
heads = ("Cache-Control", "ETag", "Last-Modified")
print(
    label,
    "card   ",
    *(f"{h}={'있음' if h in card.headers else '-'}" for h in heads),
)
# endregion

# region: list
got = rpc("ListTasks", {"contextId": "no-such-context"})
print(label, "list    tasks =", json.dumps(got.get("tasks", "(빠짐)")))
# endregion

# region: history
quote = {"data": {"date": "2026-10-30", "nights": 1, "headcount": 30}}
msg = {"messageId": "h-1", "role": "ROLE_USER", "parts": [quote]}
cfg = {"historyLength": 0}
task = rpc("SendMessage", {"message": msg, "configuration": cfg})[
    "task"
]
print(label, "history historyLength 0 →", len(task.get("history", [])))
# endregion
# @ norun
