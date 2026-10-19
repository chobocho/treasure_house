"""요청 하나에 JSON 한 줄을 남기는 ASGI 미들웨어(HTTP 층).

SDK 를 고치지 않고 앱 바깥을 감싼다. 줄은 $A2A_LOG 디렉터리의
<에이전트>.jsonl 에 붙인다($A2A_LOG 가 없으면 $TMPDIR/a2a-log).
"""

import json
import os
import tempfile
import time
from datetime import UTC, datetime

# 결과가 한 겹 싸여 오는 이름들(SendMessage·스트림 이벤트)
WRAP = ("task", "statusUpdate", "artifactUpdate", "message")


# region: line
def begin(agent, body):
    """요청 본문에서 잇는 열쇠만 꺼낸다(파트 내용은 뺀다)."""
    try:
        req = json.loads(body)
    except ValueError:
        req = {}
    p = req.get("params") or {}
    m = p.get("message") or {}
    return {
        "t": datetime.now(UTC).isoformat(timespec="milliseconds"),
        "agent": agent,
        "rpc": req.get("id"),
        "method": req.get("method"),
        "msg": m.get("messageId"),
        "ctx": m.get("contextId"),
        "task": m.get("taskId") or p.get("id"),
        "state": None,
    }


def pick(rec, obj):
    """응답 하나(스트림이면 이벤트 하나)로 줄을 채운다."""
    if "error" in obj:
        rec["state"] = f"error {obj['error'].get('code')}"
        return
    r = obj.get("result") or {}
    # GetTask·CancelTask 의 result 는 Task 그 자체다
    x = next((r[k] for k in WRAP if k in r), r)
    rec["ctx"] = x.get("contextId", rec["ctx"])
    if "taskId" in x or "status" in x:
        rec["task"] = x.get("taskId") or x.get("id")
    if "status" in x:
        rec["state"] = x["status"].get("state")


# endregion


# region: middleware
class JsonLog:
    def __init__(self, app, agent):
        self.app, self.agent = app, agent
        folder = os.environ.get("A2A_LOG") or os.path.join(
            tempfile.gettempdir(), "a2a-log"
        )
        os.makedirs(folder, exist_ok=True)
        self.path = os.path.join(folder, f"{agent}.jsonl")

    async def __call__(self, scope, receive, send):
        rpc = scope["type"] == "http" and scope["method"] == "POST"
        if not rpc or scope["path"] != "/":  # 카드·토큰 경로는 빼고
            return await self.app(scope, receive, send)
        began, body, out, sse = time.perf_counter(), [], [], [False]

        async def take():  # 요청 본문을 흘려 보내며 베껴 둔다
            m = await receive()
            body.append(m.get("body", b""))
            return m

        async def give(m):  # 응답도 마찬가지
            if m["type"] == "http.response.start":
                ct = dict(m["headers"]).get(b"content-type", b"")
                sse[0] = ct.startswith(b"text/event-stream")
            else:
                out.append(m.get("body", b""))
            await send(m)

        try:
            await self.app(scope, take, give)
        finally:  # 끊겨도 한 줄은 남긴다
            self.write(b"".join(body), b"".join(out), sse[0], began)

    # endregion

    def write(self, body, out, sse, began):
        rec = begin(self.agent, body)
        lines = out.splitlines() if sse else [out]
        for ln in lines:
            if sse and not ln.startswith(b"data:"):
                continue
            try:
                pick(rec, json.loads(ln[5:] if sse else ln))
            except ValueError:
                pass  # 빈 본문 따위
        took = (time.perf_counter() - began) * 1000
        rec["took"] = f"{took:.1f}ms"
        with open(self.path, "a", encoding="utf-8") as f:
            line = json.dumps(
                rec, ensure_ascii=False, separators=(",", ":")
            )
            f.write(line + "\n")


# @ norun
