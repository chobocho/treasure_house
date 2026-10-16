# GetTask·CancelTask 의 인자를 ProtoJSON 이 허락하는 다른 꼴로 —
# historyLength 를 문자열 "2" 로, id 를 수 5 로. urllib 만 쓴다.
#   python 06/params_probe.py 주소
import json
import sys
import urllib.request

URL = sys.argv[1]
N = iter(range(1, 100))  # messageId 와 JSON-RPC id 를 매기는 번호


# region: rpc
def rpc(method, params):
    """JSON-RPC 한 번 → result, 또는 error 객체."""
    n = next(N)
    body = {"jsonrpc": "2.0", "id": n, "method": method}
    body["params"] = params
    head = {"Content-Type": "application/json", "A2A-Version": "1.0"}
    req = urllib.request.Request(URL, json.dumps(body).encode(), head)
    with urllib.request.urlopen(req) as r:
        resp = json.load(r)
    return resp.get("result", resp.get("error"))


def say(text, task=None):
    msg = {"messageId": f"m-{next(N)}", "role": "ROLE_USER"}
    msg |= {"taskId": task} if task else {}
    msg["parts"] = [{"text": text}]
    return rpc("SendMessage", {"message": msg})["task"]


def show(step, got):
    """작업이면 상태와 이력 수, 오류면 code·message 와 짚은 곳."""
    if "code" not in got:
        n = len(got.get("history", []))
        print(f"{step:28} → {got['status']['state'][11:]} 이력 {n}개")
        return
    info = (got.get("data") or [{}])[0]
    meta = info.get("metadata", {})
    bad = info.get("fieldViolations", [{}])[0].get("field")
    where = bad or (
        "taskId=" + json.dumps(meta["taskId"])
        if "taskId" in meta
        else ""
    )
    print(f"{step:28} → {got['code']} {got['message'][:44]} {where}")


# endregion


# region: probe
done = say("2026-10-30 1박 숙소 부탁합니다")
done = say("30명", task=done["id"])  # 이력: 물음 → 답, 셋
tid = done["id"]
for hl in (2, "2"):
    params = {"id": tid, "historyLength": hl}
    show(
        f"GetTask historyLength {json.dumps(hl)}",
        rpc("GetTask", params),
    )
show("GetTask id 5", rpc("GetTask", {"id": 5}))
show("CancelTask id 5", rpc("CancelTask", {"id": 5}))
# endregion
# @ norun
