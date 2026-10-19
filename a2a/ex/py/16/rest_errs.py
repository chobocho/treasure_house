# 3장의 오류를 HTTP+JSON 문으로 — 13부의 REST 숙소 에이전트에 보낸다.
# 한 경우에 한 줄: 서버 이름, 경우, HTTP 상태, error.status,
# ErrorInfo 의 reason(없으면 -), 그리고 서버가 쓴 message 그대로.
#   python 16/rest_errs.py LABEL PORT
import sys

import httpx

label, port = sys.argv[1], sys.argv[2]
http = httpx.Client(
    base_url=f"http://127.0.0.1:{port}", headers={"A2A-Version": "1.0"}
)
QUOTE = {"data": {"date": "2026-10-30", "nights": 1, "headcount": 30}}


def msg(n, part, **more):
    m = {"messageId": f"m-{n}", "role": "ROLE_USER", "parts": [part]}
    return {"message": {**m, **more}}


# region: show
def show(case, r):
    try:
        body = r.json()
    except ValueError:
        print(label, f"{case:<11}", r.status_code, "(JSON 아님)")
        return {}
    e = body.get("error") if isinstance(body, dict) else None
    if not isinstance(e, dict):
        print(label, f"{case:<11}", r.status_code, "-")
        return body
    why = [d.get("reason") for d in e.get("details") or []]
    print(
        label,
        f"{case:<11}",
        r.status_code,
        e.get("status"),
        ([w for w in why if w] or ["-"])[0],
        e.get("message"),
    )
    return body


# endregion

# region: calls
show("not-found", http.get("/tasks/no-such-task"))
task = show("setup", http.post("/message:send", json=msg(1, QUOTE)))
tid, ctx = task["task"]["id"], task["task"]["contextId"]
show("cancel-done", http.post(f"/tasks/{tid}:cancel"))
hook = {"url": "http://127.0.0.1:9/hook"}
show(
    "push",
    http.post(f"/tasks/{tid}/pushNotificationConfigs", json=hook),
)
show("xcard", http.get("/extendedAgentCard"))
again = msg(2, {"text": "30명"}, taskId=tid, contextId=ctx)
show("send-done", http.post("/message:send", json=again))
show("page-size", http.get("/tasks", params={"pageSize": 1000}))
v99 = {"A2A-Version": "9.9"}
show("ver-9.9", http.get("/tasks/no-such-task", headers=v99))
# endregion
# @ norun
