# 맨손 서버 하나에 SendStreamingMessage 네 번 — 새 작업, 이어 말하기,
# 끝난 작업에 또(오류), 받자마자 거절. 이벤트마다 한 줄씩 찍는다.
# urllib 만 쓴다 — SSE 는 2부의 규칙대로 줄을 읽어 손으로 자른다.
#   python 06/stream_turns.py 주소
import json
import sys
import urllib.request

URL = sys.argv[1]
N = iter(range(1, 100))  # messageId 와 JSON-RPC id 를 매기는 번호


# region: open
def stream(*parts, task=None, ctx=None):
    """SendStreamingMessage 한 번 → (Content-Type, 응답들의 목록)."""
    n = next(N)
    msg = {"messageId": f"m-{n}", "role": "ROLE_USER"}
    msg |= {"taskId": task, "contextId": ctx} if task else {}
    msg["parts"] = list(parts)
    body = {"jsonrpc": "2.0", "id": n, "method": "SendStreamingMessage"}
    body["params"] = {"message": msg}
    head = {"Content-Type": "application/json", "A2A-Version": "1.0"}
    req = urllib.request.Request(URL, json.dumps(body).encode(), head)
    with urllib.request.urlopen(req) as r:
        ctype = r.headers.get("Content-Type")
        if ctype != "text/event-stream":  # 오류는 JSON 하나로 온다
            return ctype, [json.load(r)]
        # data 줄을 모으다 빈 줄에서 이벤트 하나(2부의 규칙)
        out, data = [], []
        for raw in r:
            line = raw.decode().rstrip("\r\n")
            if line.startswith("data:"):
                data.append(line[5:].lstrip(" "))
            elif not line and data:
                out.append(json.loads("\n".join(data)))
                data = []
        return ctype, out


# endregion


# region: show
def show(step, got):
    """응답 하나에 한 줄 — 종류와 상태(또는 아티팩트 이름·오류)."""
    ctype, resps = got
    print(f"{step} — {ctype}, 응답 {len(resps)}개")
    for resp in resps:
        if "error" in resp:
            err = resp["error"]
            print(f"   id {resp['id']} error {err['code']}")
            continue
        ((kind, ev),) = resp["result"].items()
        what = (
            ev["artifact"]["name"]
            if kind == "artifactUpdate"
            else ev["status"]["state"][11:]
        )
        print(f"   id {resp['id']} {kind:<14} {what}")
    return resps[0].get("result", {}).get("task", {})


# endregion


# region: turns
first = show(
    "① 새 작업(날짜·박 수)",
    stream(
        {"text": "숙소 부탁합니다"},
        {"data": {"date": "2026-10-30", "nights": 1}},
    ),
)
tid, cid = first["id"], first["contextId"]
show(
    "② 이어 말하기 '30명'", stream({"text": "30명"}, task=tid, ctx=cid)
)
show("③ 끝난 작업에 또", stream({"text": "40명"}, task=tid, ctx=cid))
show(
    "④ 문 닫은 날(12-31)",
    stream(
        {"data": {"date": "2026-12-31", "nights": 1, "headcount": 30}}
    ),
)
# endregion
# @ norun
