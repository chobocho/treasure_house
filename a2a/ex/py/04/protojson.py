# ProtoJSON 규칙을 비튼 요청 본문(run/04/rpc/pj_*.json)을 맨손
# JSON-RPC 로 보내고, 서버가 받았는지(상태·저장된 role) 거절했는지
# (오류 코드·문구) 한 줄씩 찍는다. 첫 답의 시각은 꼴만 찍는다.
#   python 04/protojson.py 주소 이름…
import json
import re
import sys
import urllib.request

RPC = "../run/04/rpc/pj_{}.json"


def post(url, body):
    head = {"Content-Type": "application/json", "A2A-Version": "1.0"}
    req = urllib.request.Request(url, body, head)
    with urllib.request.urlopen(req) as r:
        return json.load(r)


# region: shape
UNIT = {0: "초", 3: "밀리초", 6: "마이크로초", 9: "나노초"}


def shape(stamps):
    """시각의 꼴만: 몇 자리까지 적었나와 시간대(값은 매번 다르다).

    끝자리 0 을 지우는 SDK 가 있어(…12.345000 → .345) 한 개만 보면
    드물게 짧게 보인다. 받은 시각 전부에서 가장 긴 것을 3자리 단위로.
    """
    rx = r"[\d-]{10}T[\d:]{8}(\.\d+)?(Z|[+-][\d:]{5})"
    ms = [re.fullmatch(rx, ts) for ts in stamps]
    digits = max(len(m[1]) - 1 if m[1] else 0 for m in ms)
    return f"{UNIT[-(-digits // 3) * 3]}까지, 시간대 {ms[0][2]}"


# endregion

url, names = sys.argv[1], sys.argv[2:]
stamps = []
for name in names:
    with open(RPC.format(name), "rb") as f:
        res = post(url, f.read())
    if "error" in res:
        e = res["error"]
        print(f"{name:8} → {e['code']} {e['message']}")
        for d in e.get("data") or []:  # 파이썬은 까닭을 여기 적는다
            for v in d.get("fieldViolations", []):
                print(f"{'':11}{v['field']}: {v['description']}")
        continue
    task = res["result"]["task"]
    state = task["status"]["state"].removeprefix("TASK_STATE_")
    role = task["history"][0].get("role", "(없음)")
    print(f"{name:8} → {state} role={role}")
    stamps.append(task["status"]["timestamp"])
print(f"{'':8}   시각: {shape(stamps)}")

# region: states
# 입력에 TaskState 가 오는 곳: ListTasks 의 status 필터
for status in ("TASK_STATE_INPUT_REQUIRED", "input-required", 6):
    q = {"jsonrpc": "2.0", "id": 2, "method": "ListTasks"}
    q["params"] = {"status": status}
    res = post(url, json.dumps(q).encode())
    if "error" in res:
        got = f"{res['error']['code']} {res['error']['message']}"
    elif "tasks" not in (r := res["result"]):
        got = "tasks 가 빠짐"  # 빈 목록을 적는 법이 셋이다
    elif not r["tasks"]:  # [] 또는 null
        got = f"tasks: {json.dumps(r['tasks'])}"
    else:
        got = f"tasks: 작업 {len(r['tasks'])}개"
    print(f"ListTasks status={status!r} → {got}")
# endregion
# @ norun
