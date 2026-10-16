# 막는 SendMessage 한 번, 잠깐 쉬고 GetTask 한 번 — 상태만 찍는다.
# SDK 없이 urllib 로 JSON-RPC 를 보낸다(어느 SDK 의 손도 타지 않게).
#   python 05/poke.py 주소 [첫말]
import json
import sys
import time
import urllib.request

URL = sys.argv[1]
TEXT = sys.argv[2] if len(sys.argv) > 2 else "시작해 주세요"


def rpc(method, params):
    body = {"jsonrpc": "2.0", "id": 1, "method": method}
    body["params"] = params
    head = {"Content-Type": "application/json", "A2A-Version": "1.0"}
    req = urllib.request.Request(URL, json.dumps(body).encode(), head)
    with urllib.request.urlopen(req) as r:
        return json.load(r)["result"]


def state(task):
    return task["status"]["state"].removeprefix("TASK_STATE_")


# region: poke
msg = {"messageId": "poke-1", "role": "ROLE_USER"}
msg["parts"] = [{"text": TEXT}]
task = rpc("SendMessage", {"message": msg})["task"]
print("SendMessage →", state(task))
time.sleep(0.5)  # 실행기가 뒤늦게 싣는 것까지 처리되도록
print("GetTask     →", state(rpc("GetTask", {"id": task["id"]})))
# endregion
# @ norun
