# 말 한마디씩 막는 SendMessage 로 보내고, 답의 상태와 그 까닭
# (status.message 의 글) 또는 오류(code·message)를 한 줄로 찍는다.
# 오류였으면 그 맥락의 작업을 ListTasks 로 찾아 저장된 상태를 본다.
# SDK 없이 urllib 로 JSON-RPC 를 보낸다(어느 SDK 의 손도 타지 않게).
#   python 05/outcome.py 주소 말 [말 …]
import json
import sys
import urllib.request

URL = sys.argv[1]


def rpc(method, params):
    body = {"jsonrpc": "2.0", "id": 1, "method": method}
    body["params"] = params
    head = {"Content-Type": "application/json", "A2A-Version": "1.0"}
    req = urllib.request.Request(URL, json.dumps(body).encode(), head)
    with urllib.request.urlopen(req) as r:
        return json.load(r)


def why(status):
    parts = status.get("message", {}).get("parts", [])
    return " ".join(p["text"] for p in parts if "text" in p)


# region: outcome
for i, word in enumerate(sys.argv[2:], 1):
    ctx = f"ctx-{i}"  # 맥락 id 를 지어 보낸다 — 나중에 찾으려고
    msg = {"messageId": f"m-{i}", "role": "ROLE_USER"}
    msg |= {"contextId": ctx, "parts": [{"text": word}]}
    reply = rpc("SendMessage", {"message": msg})
    if "error" in reply:  # JSON-RPC 오류 — 답에 Task 가 없다
        e = reply["error"]
        print(f"{word} → 오류 {e['code']} {e['message']}")
        found = rpc("ListTasks", {"contextId": ctx})["result"]
        tasks = found.get("tasks") or []  # Go 서버는 빈 목록이 null
        states = [t["status"]["state"] for t in tasks]
        print("  저장된 작업:", states or "없음")
        continue
    status = reply["result"]["task"]["status"]
    state = status["state"].removeprefix("TASK_STATE_")
    print(f"{word} → {state} | {why(status) or '(까닭 없음)'}")
# endregion
# @ norun
