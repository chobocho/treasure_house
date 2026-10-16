# 두 마디 — "워크숍 접수"(인원이 없어 되묻는다), 그 작업에 "30명" —
# 그리고 GetTask 로 이력을 본다. SDK 없이 urllib 로 JSON-RPC 를 보낸다.
#   python 05/twice.py 주소
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


def say(mid, text, task=None):
    msg = {"messageId": mid, "role": "ROLE_USER"}
    msg["parts"] = [{"text": text}]
    if task:  # 이어 말하기 — 같은 taskId·contextId
        msg["taskId"], msg["contextId"] = task["id"], task["contextId"]
    t = rpc("SendMessage", {"message": msg})["task"]
    print(f"{text} → {t['status']['state']}")
    return t


# region: twice
task = say("m-1", "워크숍 접수")
say("m-2", "30명", task)
for m in rpc("GetTask", {"id": task["id"]})["history"]:
    print("  history:", m["role"], m["parts"][0]["text"])
# endregion
# @ norun
