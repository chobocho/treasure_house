# 맨손 서버 하나와 SendMessage 를 여섯 번 — 새 작업, 이어 말하기,
# 그리고 begin 의 문 셋(끝난 작업·어긋난 contextId·없는 작업).
# urllib 만 쓴다 — 어느 SDK 의 손도 타지 않은 바이트를 보내려고.
#   python 06/turns.py 주소
import json
import sys
import urllib.request

URL = sys.argv[1]
N = iter(range(1, 100))  # messageId 와 JSON-RPC id 를 매기는 번호


# region: rpc
def send(*parts, task=None, ctx=None):
    """SendMessage 한 번 → 결과의 task, 또는 error 객체."""
    n = next(N)
    msg = {"messageId": f"m-{n}", "role": "ROLE_USER"}
    msg |= {
        k: v for k, v in (("taskId", task), ("contextId", ctx)) if v
    }
    msg["parts"] = list(parts)
    body = {"jsonrpc": "2.0", "id": n, "method": "SendMessage"}
    body["params"] = {"message": msg}
    head = {"Content-Type": "application/json", "A2A-Version": "1.0"}
    req = urllib.request.Request(URL, json.dumps(body).encode(), head)
    with urllib.request.urlopen(req) as r:
        resp = json.load(r)
    return resp["result"]["task"] if "result" in resp else resp["error"]


def show(step, got):
    """한 줄 — 상태와 에이전트의 말, 또는 오류 code 와 그 이름."""
    if "code" in got:
        info = got["data"][0]
        why = info.get("reason") or info["fieldViolations"][0]["field"]
        print(f"{step} → {got['code']} {why}")
        return
    st = got["status"]
    said = st.get("message", {}).get("parts", [{}])[0].get("text", "")
    arts = [
        p["text"]
        for a in got.get("artifacts", [])
        for p in a["parts"]
        if "text" in p
    ]
    print(f"{step} → {st['state'][11:]} {said}{' '.join(arts)}")


# endregion


# region: turns
first = send(
    {"text": "숙소 부탁합니다"},
    {"data": {"date": "2026-10-30", "nights": 1}},
)
show("① 새 작업(날짜·박 수)", first)
tid, cid = first["id"], first["contextId"]
show("② 이어 말하기 '30명'", send({"text": "30명"}, task=tid, ctx=cid))
show("③ 끝난 작업에 또", send({"text": "40명"}, task=tid, ctx=cid))

other = send({"text": "숙소 부탁합니다"})
show("④ 새 작업(글만)", other)
show(
    "⑤ 어긋난 contextId",
    send({"text": "1박"}, task=other["id"], ctx=cid),
)
show(
    "⑥ taskId 만으로",
    send({"text": "2026-11-06 1박 30명"}, task=other["id"]),
)
show("⑦ 없는 taskId", send({"text": "30명"}, task="nope"))
# endregion
# @ norun
