# 배차를 맡기고(returnImmediately), 첫 단계가 지나면 곧 취소한다.
# 취소를 한 번 더 보내 보고, 마지막에 GetTask 로 저장된 상태를 본다.
# SDK 없이 urllib 로 JSON-RPC 를 보낸다(어느 SDK 의 손도 타지 않게).
#   python 05/cancel.py 주소 엿볼주소
# 엿볼주소는 탭을 거치지 않는 서버 주소 — 몇 번 엿봤는지는 기계의
# 빠르기에 따라 달라, 와이어 기록에 남기지 않는다.
import json
import sys
import time
import urllib.request

URL, PEEK = sys.argv[1], sys.argv[2]


def rpc(method, params, url=URL):
    body = {"jsonrpc": "2.0", "id": 1, "method": method}
    body["params"] = params
    head = {"Content-Type": "application/json", "A2A-Version": "1.0"}
    req = urllib.request.Request(url, json.dumps(body).encode(), head)
    with urllib.request.urlopen(req) as r:
        return json.load(r)


def show(name, reply):
    if "error" in reply:
        e = reply["error"]
        print(f"{name} → 오류 {e['code']} {e['message']}")
        return
    status = reply["result"].get("task", reply["result"])["status"]
    parts = status.get("message", {}).get("parts", [])
    words = " ".join(p["text"] for p in parts if "text" in p)
    state = status["state"].removeprefix("TASK_STATE_")
    print(f"{name} → {state} | {words or '(글 없음)'}")


# region: cancel
order = {"headcount": 30, "nights": 1, "depart": "강남역"}
msg = {"messageId": "bus-1", "role": "ROLE_USER"}
msg["parts"] = [{"data": order}]
now = {"returnImmediately": True}
sent = rpc("SendMessage", {"message": msg, "configuration": now})
show("SendMessage ", sent)
tid = sent["result"]["task"]["id"]
while True:  # 첫 단계(WORKING)가 지날 때까지 엿본다
    peek = rpc("GetTask", {"id": tid}, PEEK)["result"]
    if peek["status"]["state"] == "TASK_STATE_WORKING":
        break
    time.sleep(0.1)
show("CancelTask ①", rpc("CancelTask", {"id": tid}))
show("CancelTask ②", rpc("CancelTask", {"id": tid}))  # 또 한 번
time.sleep(0.5)  # 실행기가 정말 멈췄는지 — 늦은 갱신이 없나
show("GetTask     ", rpc("GetTask", {"id": tid}))
# endregion
# @ norun
