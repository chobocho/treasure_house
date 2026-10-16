# 맨손 서버 하나에 GetTask 여섯 번(historyLength 를 바꿔 가며)과
# CancelTask 다섯 번. urllib 만 쓴다.
#   python 06/get_cancel.py 주소
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


def say(*parts, task=None):
    """SendMessage — 이어 말하기면 taskId 만 단다(맥락은 서버가 찾는다)."""
    msg = {"messageId": f"m-{next(N)}", "role": "ROLE_USER"}
    msg |= {"taskId": task} if task else {}
    msg["parts"] = list(parts)
    return rpc("SendMessage", {"message": msg})["task"]


def show(step, got):
    """작업이면 상태와 이력의 role 들, 오류면 code 와 이름."""
    if "code" in got:
        info = got["data"][0]
        why = info.get("reason") or info["fieldViolations"][0]["field"]
        print(f"{step} → {got['code']} {why}")
        return
    roles = [m["role"][5:] for m in got.get("history", [])]
    hist = " ".join(roles) or "(history 없음)"
    print(f"{step} → {got['status']['state'][11:]} {hist}")


# endregion


# region: get
done = say(
    {"text": "숙소 부탁합니다"},
    {"data": {"date": "2026-10-30", "nights": 1}},
)
done = say({"text": "30명"}, task=done["id"])
for hl in (None, 0, 1, 2, 5, -1):
    params = {"id": done["id"]}
    params |= {} if hl is None else {"historyLength": hl}
    label = "없음" if hl is None else hl
    show(f"GetTask historyLength {label}", rpc("GetTask", params))
show("GetTask 없는 id", rpc("GetTask", {"id": "nope"}))
# endregion

# region: cancel
wait = say({"text": "숙소 부탁합니다"})  # 날짜를 되묻고 멈춘다
once = rpc("CancelTask", {"id": wait["id"]})
show("CancelTask 기다리는 작업", once)
again = rpc("CancelTask", {"id": wait["id"]})
show("CancelTask 한 번 더", again)
print("  두 답이 같다:", again == once)
late = {
    "messageId": "m-late",
    "role": "ROLE_USER",
    "taskId": wait["id"],
}
late["parts"] = [{"text": "2026-10-30"}]
show("취소된 작업에 이어 말하기", rpc("SendMessage", {"message": late}))
show("CancelTask 끝난 작업", rpc("CancelTask", {"id": done["id"]}))
show("CancelTask 없는 id", rpc("CancelTask", {"id": "nope"}))
# endregion
# @ norun
