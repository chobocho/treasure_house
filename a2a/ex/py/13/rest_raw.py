# SDK 없이 HTTP+JSON 문을 두드린다 — 경로·동사·상태 코드만 본다.
# 몸통은 탭이 적으므로 여기서는 한 요청에 한 줄씩 요약한다.
#   python 13/rest_raw.py http://127.0.0.1:P/
import sys

import httpx

base = sys.argv[1].rstrip("/")
http = httpx.Client(headers={"A2A-Version": "1.0"})
send = {
    "message": {
        "messageId": "m-1",
        "role": "ROLE_USER",
        "parts": [{"text": "2026-10-30 1박 30명"}],
    }
}


# region: show
def show(r, what):
    kind = r.headers.get("content-type", "-").split(";")[0]
    head = f"{r.request.method:4} {r.status_code} {kind:20}"
    try:
        body = r.json()
    except ValueError:
        print(head, "(JSON 아님)", what)
        return {}
    if "error" in body and isinstance(body["error"], dict):
        e = body["error"]
        why = [d.get("reason") for d in e.get("details") or []]
        print(head, e.get("status"), why, what)
    else:
        print(head, what)
    return body


# endregion

# region: calls
task = show(http.post(base + "/message:send", json=send), "보내기")
tid, ctx = task["task"]["id"], task["task"]["contextId"]
got = show(http.get(f"{base}/tasks/{tid}?historyLength=0"), "읽기")
print(
    "     state:",
    got["status"]["state"],
    "history:",
    len(got.get("history", [])),
)
lst = show(http.get(f"{base}/tasks", params={"contextId": ctx}), "목록")
print("     tasks:", len(lst["tasks"]))
show(http.post(f"{base}/tasks/{tid}:cancel"), "끝난 작업 취소")
show(http.get(f"{base}/tasks/t-nope"), "없는 작업")
bad = b'{"message": {"messageId": "m-2"'  # 닫히지 않은 JSON
hdr = {"Content-Type": "application/json"}
show(
    http.post(base + "/message:send", content=bad, headers=hdr),
    "깨진 JSON",
)
show(http.get(base + "/nope"), "없는 경로")
show(
    http.post(base + "/bosang-hq/message:send", json=send),
    "tenant 경로",
)
# endregion
# @ norun
