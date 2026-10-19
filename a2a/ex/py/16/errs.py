# 오류를 일부러 일으키는 맨손 JSON-RPC 탐침. SDK 없이 httpx 로 보낸다.
# 한 경우에 한 줄: 서버 이름, 경우, HTTP 상태, 꼴(json·sse), 코드,
# ErrorInfo 의 reason(없으면 -), 그리고 서버가 쓴 message 그대로.
#   python 16/errs.py LABEL PORT SET...   SET = std data a2a bench
#                                               ctype ext
import json
import sys

import httpx

label, port, sets = sys.argv[1], sys.argv[2], sys.argv[3:]
url = f"http://127.0.0.1:{port}/"
HEAD = {"Content-Type": "application/json", "A2A-Version": "1.0"}


def rpc(method, params, n=1):
    return {
        "jsonrpc": "2.0",
        "id": n,
        "method": method,
        "params": params,
    }


seq = iter(range(1, 100))


def msg(*parts, **more):
    m = {"messageId": f"m-{next(seq)}", **more}
    return {"message": {**m, "role": "ROLE_USER", "parts": list(parts)}}


QUOTE = {"data": {"date": "2026-10-30", "nights": 1, "headcount": 30}}


# region: show
def show(case, body, head=None, raw=None):
    h = {k: v for k, v in {**HEAD, **(head or {})}.items() if v}
    data = raw if raw is not None else json.dumps(body)
    with httpx.stream("POST", url, content=data, headers=h) as r:
        sse = "event-stream" in r.headers["content-type"]
        kind = "sse" if sse else "json"
        if sse:  # 첫 data: 줄만 읽는다
            lines = (ln for ln in r.iter_lines() if ln[:5] == "data:")
            reply = json.loads(next(lines)[5:])
        else:
            reply = json.loads(r.read())
    err = reply.get("error")
    if err is None:
        res = reply["result"]
        got = res.get("task", res).get("status", {}).get("state")
        what = "result " + (got or next(iter(res)))
        print(label, f"{case:<11}", r.status_code, kind, what)
        return res
    why = [
        d.get("reason") for d in err.get("data") or [] if "reason" in d
    ]
    print(
        label,
        f"{case:<11}",
        r.status_code,
        kind,
        err["code"],
        (why or ["-"])[0],
        err["message"],
    )


# endregion


def done():
    """끝난(COMPLETED) 숙소 작업 하나를 만들어 둔다."""
    t = show("setup", rpc("SendMessage", msg(QUOTE)))["task"]
    return t["id"], t["contextId"]


# region: std
def std():
    show("parse", None, raw='{"jsonrpc": "2.0", "id": 1, "method": ')
    show("array", None, raw="[]")
    show(
        "jsonrpc1.0", {**rpc("GetTask", {"id": "x"}), "jsonrpc": "1.0"}
    )
    show("no-method", {"jsonrpc": "2.0", "id": 1, "params": {}})
    show("method", rpc("NoSuchMethod", {}))
    show("no-id", rpc("GetTask", {}))
    show("id-number", rpc("GetTask", {"id": 5}))
    show("page-size", rpc("ListTasks", {"pageSize": 1000}))


# endregion


# region: data
def data():
    bad = {
        "data": {"date": "2026-10-30", "nights": 1, "headcount": "서른"}
    }
    show("bad-data", rpc("SendMessage", msg(bad)))


# endregion


# region: a2a
def a2a():
    nope = {"id": "no-such-task"}
    show("not-found", rpc("GetTask", nope))
    show("cancel-nf", rpc("CancelTask", nope))
    tid, ctx = done()
    show("cancel-done", rpc("CancelTask", {"id": tid}))
    hook = {"taskId": tid, "url": "http://127.0.0.1:9/hook"}
    show("push", rpc("CreateTaskPushNotificationConfig", hook))
    show("xcard", rpc("GetExtendedAgentCard", {}))
    again = msg({"text": "30명"}, taskId=tid, contextId=ctx)
    show("send-done", rpc("SendMessage", again))
    show("stream-done", rpc("SendStreamingMessage", again))
    show("sub-done", rpc("SubscribeToTask", {"id": tid}))
    show("ver-9.9", rpc("GetTask", nope), {"A2A-Version": "9.9"})
    show("ver-none", rpc("GetTask", nope), {"A2A-Version": ""})


# endregion


# region: bench
def bench():
    show("xcard", rpc("GetExtendedAgentCard", {}))
    order = msg({"text": "차례 위반"})
    show("order", rpc("SendMessage", order))
    show("order-sse", rpc("SendStreamingMessage", order))
    crash = msg({"text": "고장"})
    show("crash", rpc("SendMessage", crash))
    show("crash-sse", rpc("SendStreamingMessage", crash))


# endregion


# region: ctype
def ctype():
    png = {"url": "https://treasure-house.example/map.png"}
    png |= {"mediaType": "image/png", "filename": "map.png"}
    show("ctype", rpc("SendMessage", msg({"text": "30명"}, png)))


# endregion


# region: ext
def ext():
    show("ext", rpc("SendMessage", msg(QUOTE)))


# endregion

for s in sets:
    globals()[s]()
# @ norun
