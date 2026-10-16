# 같은 messageId 를 두 번 보낸다(SDK 없이 urllib 로 JSON-RPC).
# 새 메시지로 두 번, 그리고 같은 작업에 이어 말하기로 한 번 더.
#   python 04/dup.py 주소
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
        return json.load(r)["result"]


def send(mid, text, task_id=None):
    msg = {"messageId": mid, "role": "ROLE_USER"}
    msg["parts"] = [{"text": text}]
    if task_id:
        msg["taskId"] = task_id
    t = rpc("SendMessage", {"message": msg})["task"]
    state = t["status"]["state"].removeprefix("TASK_STATE_")
    print(f"{mid} → task {t['id']} {state}")
    return t["id"]


# region: dup
send("m-dup", "30명")  # ① 새 메시지
send("m-dup", "30명")  # ② 같은 messageId 로 또
t = send("m-ask", "워크숍 접수")  # ③ 인원이 없어 되묻는다
send("m-ask", "워크숍 접수", t)  # ④ 그 작업에 같은 messageId 로
hist = rpc("GetTask", {"id": t})["history"]
print("history:", ", ".join(m["messageId"] for m in hist))
# endregion
# @ norun
