# 작업 둘레의 오류를 차례로 일으킨다 — 없는 작업, 끝난 작업.
# 오류마다 code·message, data 의 @type·reason 과 나머지 키를 찍는다.
# SDK 없이 urllib 로 JSON-RPC 를 보낸다(어느 SDK 의 손도 타지 않게).
#   python 05/errors.py 주소
import json
import sys
import time
import urllib.request

URL = sys.argv[1]
GHOST = "t-없는-작업"  # 서버가 만든 적 없는 작업 id


def rpc(method, params):
    body = {"jsonrpc": "2.0", "id": 1, "method": method}
    body["params"] = params
    head = {"Content-Type": "application/json", "A2A-Version": "1.0"}
    req = urllib.request.Request(URL, json.dumps(body).encode(), head)
    with urllib.request.urlopen(req) as r:
        return json.load(r)


def show(name, reply):
    if "result" in reply:
        task = reply["result"].get("task", reply["result"])
        print(f"{name} → 결과 {task['status']['state']}")
        return
    e = reply["error"]
    print(f"{name} → {e['code']}")
    print(f"    message: {e['message']}")
    for d in e.get("data") or []:  # 자세한 내용(있으면)
        rest = dict(d)
        kind = rest.pop("@type", "?").rsplit(".", 1)[-1]
        print(f"    data: {kind} {rest.pop('reason', '')}".rstrip())
        print("         ", json.dumps(rest, ensure_ascii=False))


def say(mid, part, task_id=None):
    msg = {"messageId": mid, "role": "ROLE_USER", "parts": [part]}
    if task_id:
        msg["taskId"] = task_id
    return rpc("SendMessage", {"message": msg})


# region: errors
show("① GetTask    없는 작업", rpc("GetTask", {"id": GHOST}))
show("② CancelTask 없는 작업", rpc("CancelTask", {"id": GHOST}))
show("③ SendMessage 없는 작업", say("e-3", {"text": "30명"}, GHOST))
order = {"date": "2026-10-30", "nights": 1, "headcount": 30}
done = say("e-4", {"data": order})["result"]["task"]  # COMPLETED
# 파이썬 SDK 는 끝난 실행을 잠시 메모리에 두었다가 치운다. 그 사이에
# 말을 걸면 "already completed", 치운 뒤면 "in terminal state" —
# 캡처가 때에 따라 갈리지 않게 치울 틈을 준다.
time.sleep(1)
show(
    "④ SendMessage 끝난 작업",
    say("e-5", {"text": "1명 더"}, done["id"]),
)
show("⑤ CancelTask  끝난 작업", rpc("CancelTask", {"id": done["id"]}))
closed = dict(order, date="2026-12-31")  # 문 닫은 날 — REJECTED
no = say("e-6", {"data": closed})["result"]["task"]
time.sleep(1)  # ④와 같은 까닭
show(
    "⑥ SendMessage 거절된 작업", say("e-7", {"text": "다시"}, no["id"])
)
# endregion
# @ norun
