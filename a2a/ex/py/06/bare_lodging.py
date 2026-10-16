"""맨손 숙소 에이전트 — SDK 없이, 표준 라이브러리만으로 A2A v1.0.

JSON-RPC 바인딩 하나: 카드, SendMessage, GetTask, CancelTask,
SendStreamingMessage(SSE). 업무 규칙은 workshop.domain 이 정하고,
말과 기록은 완성 에이전트(agents/lodging.py)와 같다.

    python 06/bare_lodging.py --port P [--url 카드에_적을_주소]
"""

import argparse
import json
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

from bare_store import (
    CANCELED,
    COMPLETED,
    INPUT_REQUIRED,
    REJECTED,
    WORKING,
    IllegalMove,
    Store,
    add_artifact,
    can_move,
    move,
    view,
)

from workshop import domain


# region: card
def card(url):
    """완성 에이전트의 카드와 같은 필드·같은 값(3부)."""
    return {
        "name": "보물상사 숙소 에이전트",
        "description": "날짜·박 수·인원으로 가장 싼 숙소를 고릅니다.",
        "supportedInterfaces": [
            {
                "url": url,
                "protocolBinding": "JSONRPC",
                "protocolVersion": "1.0",
            }
        ],
        "provider": {
            "url": "https://treasure-house.example",
            "organization": "보물상사",
        },
        "version": "1.0.0",
        "capabilities": {"streaming": True},
        "defaultInputModes": ["application/json", "text/plain"],
        "defaultOutputModes": ["application/json"],
        "skills": [
            {
                "id": "find-lodging",
                "name": "숙소 찾기",
                "description": "워크숍 숙소를 고르고 견적을 냅니다.",
                "tags": ["lodging", "workshop"],
                "examples": [
                    '{"date":"2026-10-30","nights":1,"headcount":30}'
                ],
            }
        ],
    }


# endregion


# region: rpc-error
class RpcError(Exception):
    """JSON-RPC 의 error 객체 하나 — code·message·data."""

    def __init__(self, code, message, data=None):
        super().__init__(message)
        self.code, self.message, self.data = code, message, data

    def body(self):
        err = {"code": self.code, "message": self.message}
        if self.data:
            err["data"] = self.data
        return err


# endregion


# region: a2a-errors
GOOGLE = "type.googleapis.com/google.rpc."
# §5.4 의 A2A 오류 가운데 이 서버가 내는 넷 — 코드·문구·reason
A2A_ERRORS = {
    "TaskNotFound": (-32001, "Task not found", "TASK_NOT_FOUND"),
    "TaskNotCancelable": (
        -32002,
        "Task cannot be canceled",
        "TASK_NOT_CANCELABLE",
    ),
    "UnsupportedOperation": (
        -32004,
        "Unsupported operation",
        "UNSUPPORTED_OPERATION",
    ),
    "VersionNotSupported": (
        -32009,
        "Version not supported",
        "VERSION_NOT_SUPPORTED",
    ),
}


def a2a_error(name, **meta):
    """A2A 오류 — data 에 google.rpc.ErrorInfo 하나(§9.5)."""
    code, message, reason = A2A_ERRORS[name]
    info = {"@type": GOOGLE + "ErrorInfo", "reason": reason}
    info |= {"domain": "a2a-protocol.org", "metadata": meta}
    return RpcError(code, message, [info])


def bad_params(field, why):
    """-32602 — 어느 필드가 왜 틀렸는지 BadRequest 로(§9.5 의 예)."""
    v = {"field": field, "description": why}
    data = [{"@type": GOOGLE + "BadRequest", "fieldViolations": [v]}]
    return RpcError(-32602, "Invalid parameters", data)


# endregion


# region: version
def check_version(headers):
    """§3.6.2 — 요청의 판으로 처리하고, 모르는 판이면 -32009.

    빈 값은 0.3 으로 읽는다. 패치 번호(1.0.1 의 .1)는 보지 않는다.
    """
    asked = headers.get("A2A-Version") or "0.3"
    if asked.split(".")[:2] != ["1", "0"]:
        raise a2a_error("VersionNotSupported", version=asked)


# endregion


# region: lodging
store = Store()

# 빠진 항목을 하나씩 되묻는다. 순서가 곧 묻는 순서다.
QUESTIONS = {
    "date": "날짜는 언제입니까? (예: 2026-10-30)",
    "nights": "며칠 묵습니까? (예: 1박)",
    "headcount": "인원은 몇 명입니까?",
}
RULES = {
    "date": domain.DATE,
    "nights": domain.NIGHTS,
    "headcount": domain.HEADCOUNT,
}


def heard(task):
    """사용자가 지금까지 한 말 → 요청. DataPart 먼저, 글이 덮는다.

    에이전트의 물음은 건너뛴다 — 물음 속 '예: 1박' 은 답이 아니다.
    """
    said = [m for m in task["history"] if m["role"] == "ROLE_USER"]
    parts = [p for m in said for p in m["parts"]]
    req = {}
    for p in parts:
        if isinstance(p.get("data"), dict):
            req |= p["data"]
    for p in parts:
        for key, rx in RULES.items():
            found = rx.search(p.get("text", ""))
            if found:
                req[key] = found.group(1)
    return req


# endregion


# region: work
def lodging(task):
    """완성 에이전트의 실행기가 하는 일. 이벤트의 목록을 돌려준다."""
    req = heard(task)
    missing = [k for k in QUESTIONS if k not in req]
    if missing:
        print(f"[숙소] 되묻기: {missing}", flush=True)
        ask = [
            {"text": QUESTIONS[missing[0]]},
            {"data": {"missing": missing}},
        ]
        return [move(task, INPUT_REQUIRED, ask)]
    nights, headcount = int(req["nights"]), int(req["headcount"])
    quote = domain.choose_lodging(
        {"date": req["date"], "nights": nights, "headcount": headcount}
    )
    if not quote["ok"]:
        print(f"[숙소] 거절: {quote['reason']}", flush=True)
        return [move(task, REJECTED, [{"text": quote["reason"]}])]
    summary = (
        f"{quote['venueName']} {quote['rooms']}실, {quote['total']:,}원"
    )
    print(f"[숙소] 견적: {summary}", flush=True)
    parts = [{"data": quote}, {"text": summary}]
    return [
        add_artifact(task, "숙소 견적", parts),
        move(task, COMPLETED),
    ]


# endregion


# region: check
CONTENT = {"text", "raw", "url", "data"}  # Part 의 oneof(4부)


def check_message(params):
    """SendMessageRequest.message 의 필수 필드(§5.7) — 틀리면 -32602."""
    msg = params.get("message")
    if not isinstance(msg, dict):
        raise bad_params("message", "메시지가 없습니다")
    if (
        not isinstance(msg.get("messageId"), str)
        or not msg["messageId"]
    ):
        raise bad_params("message.messageId", "비어 있습니다")
    if msg.get("role") != "ROLE_USER":
        raise bad_params("message.role", "ROLE_USER 여야 합니다")
    parts = msg.get("parts")
    if not isinstance(parts, list) or not parts:
        raise bad_params("message.parts", "파트가 하나도 없습니다")
    for p in parts:
        if not isinstance(p, dict) or len(CONTENT & p.keys()) != 1:
            why = "text·raw·url·data 중 하나만 있어야 합니다"
            raise bad_params("message.parts", why)
    return msg


def find(task_id):
    """id 로 작업을 찾는다 — 없으면 -32001(§3.4.2)."""
    task = store.get(task_id) if isinstance(task_id, str) else None
    if task is None:
        raise a2a_error("TaskNotFound", taskId=str(task_id))
    return task


# endregion


# region: begin
def begin(params):
    """두 Send 메서드의 앞부분 — 새 작업이거나 이어 말하기다."""
    msg = check_message(params)
    if not msg.get("taskId"):
        return store.create(msg)
    task = find(msg["taskId"])
    if (msg.get("contextId") or task["contextId"]) != task["contextId"]:
        why = "작업의 contextId 와 다릅니다"  # §3.4.3
        raise bad_params("message.contextId", why)
    if not can_move(task["status"]["state"], WORKING):
        # 종료 상태 — 표에 나갈 곳이 없다(§3.1.1)
        raise a2a_error("UnsupportedOperation", taskId=task["id"])
    move(task, WORKING)  # 지난 물음은 이 때 이력으로 내려간다
    store.append(task, msg)
    return task


# endregion


# region: send
def send_message(params):
    """막는 호출 — 끝나거나 멈출 때까지 다 하고 Task 를 돌려준다."""
    config = params.get("configuration") or {}
    n = history_length(config.get("historyLength"))
    task = begin(params)
    lodging(task)  # 이벤트는 버린다 — 결과는 저장소의 Task 에
    return {"task": view(task, n)}


# endregion


# region: get
def history_length(raw):
    """historyLength — 없으면 전부, 0 이상의 정수만 받는다."""
    if raw is None:
        return None
    if type(raw) is not int or raw < 0:
        raise bad_params("historyLength", "0 이상의 정수여야 합니다")
    return raw


def get_task(params):
    n = history_length(params.get("historyLength"))
    return view(find(params.get("id")), n)


# endregion


# region: cancel
def cancel_task(params):
    """취소 — 이미 CANCELED 면 그대로 돌려준다(§3.3.1 멱등)."""
    task = find(params.get("id"))
    state = task["status"]["state"]
    if state != CANCELED:
        if not can_move(state, CANCELED):
            raise a2a_error("TaskNotCancelable", taskId=task["id"])
        move(task, CANCELED)
    return view(task)


# endregion


# region: stream
def send_streaming_message(params):
    """스트림 — 첫 이벤트는 늘 Task 다(§3.1.2). 이어 말할 때도.

    돌려주는 것은 StreamResponse 의 목록. 숙소 일은 기다릴 것이
    없어 한 번에 다 나오고, 내보내기(SSE)는 http 쪽이 한다.
    """
    task = begin(params)
    first = {"task": view(task)}  # 지금 모습을 먼저 떠 둔다
    return [first, *lodging(task)]


# endregion


# region: methods
# 메서드 이름(§9.4, PascalCase) → (처리 함수, 답이 SSE 스트림인가)
METHODS = {
    "SendMessage": (send_message, False),
    "SendStreamingMessage": (send_streaming_message, True),
    "GetTask": (get_task, False),
    "CancelTask": (cancel_task, False),
}
# endregion


# region: dispatch
def dispatch(body, headers):
    """본문 → (JSON-RPC 응답, None) 또는 (None, 스트림 응답들)."""
    try:
        req = json.loads(body)
    except ValueError:
        return failure(None, RpcError(-32700, "Invalid JSON payload"))
    # 배치(배열)와 알림(id 없음)은 받지 않는다 — A2A 는 늘 답을 준다
    if (
        not isinstance(req, dict)
        or req.get("jsonrpc") != "2.0"
        or not isinstance(req.get("method"), str)
        or not isinstance(req.get("id"), (str, int))
    ):
        why = "Request payload validation error"
        return failure(None, RpcError(-32600, why))
    try:
        result, streams = call(req, headers)
    except RpcError as e:
        return failure(req["id"], e)
    # 우리 코드가 깨졌다 — 전이 표 위반(버그)이나 이상한 입력값
    except (IllegalMove, ValueError, KeyError, TypeError) as e:
        print(f"[숙소] 내부 오류: {e!r}", file=sys.stderr, flush=True)
        return failure(req["id"], RpcError(-32603, "Internal error"))
    if streams:
        return None, [ok(req["id"], ev) for ev in result]
    return ok(req["id"], result), None


# endregion


# region: call
def call(req, headers):
    """판·메서드·인자를 보고 처리 함수를 부른다 → (결과, 스트림인가)."""
    check_version(headers)  # 판이 메서드 이름의 뜻을 정한다
    if req["method"] not in METHODS:
        raise RpcError(-32601, "Method not found")
    fn, streams = METHODS[req["method"]]
    params = req.get("params")
    if not isinstance(params, dict):
        raise bad_params("params", "객체여야 합니다")
    return fn(params), streams


def ok(rid, result):
    return {"jsonrpc": "2.0", "id": rid, "result": result}


def failure(rid, err):
    return {"jsonrpc": "2.0", "id": rid, "error": err.body()}, None


# endregion


# region: http
class Handler(BaseHTTPRequestHandler):
    """경로 둘 — GET 카드, POST / (JSON-RPC). 나머지는 404."""

    def do_GET(self):
        if self.path != "/.well-known/agent-card.json":
            return self.send_error(404)
        self.reply(CARD)

    def do_POST(self):
        if self.path != "/":
            return self.send_error(404)
        size = int(self.headers.get("Content-Length", 0))
        resp, events = dispatch(self.rfile.read(size), self.headers)
        if events is None:
            return self.reply(resp)
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.end_headers()
        for ev in events:  # 이벤트 하나 = data 줄 + 빈 줄(2부)
            line = json.dumps(ev, ensure_ascii=False)
            self.wfile.write(f"data: {line}\n\n".encode())
            self.wfile.flush()

    def reply(self, obj):
        data = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):
        pass  # 요청마다 찍는 접속 기록은 끈다


# endregion


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="맨손 숙소 에이전트")
    ap.add_argument("--port", type=int, required=True)
    ap.add_argument("--url", help="카드에 적을 주소(기본: 붙는 주소)")
    args = ap.parse_args()
    CARD = card(args.url or f"http://127.0.0.1:{args.port}/")
    # 한 번에 한 요청 — 스레드가 없으니 저장소에 자물쇠도 없다
    HTTPServer(("127.0.0.1", args.port), Handler).serve_forever()
# @ norun
