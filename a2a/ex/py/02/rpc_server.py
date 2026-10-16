# JSON-RPC 2.0 서버 — http.server 와 json 만으로. 메서드는 하나,
# ChooseLodging(숙소 고르기). 알림과 배치까지 JSON-RPC 2.0 대로.
import argparse
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

from workshop.domain import choose_lodging

ap = argparse.ArgumentParser()
ap.add_argument("--port", type=int, required=True)
args = ap.parse_args()


# region: errors
def error(code, message, rid=None):
    err = {"code": code, "message": message}
    return {"jsonrpc": "2.0", "id": rid, "error": err}


def lodging_params(p):
    """date 는 문자열, nights·headcount 는 정수여야 한다."""
    return (
        isinstance(p, dict)
        and type(p.get("date")) is str
        and type(p.get("nights")) is int  # bool 은 int 가 아니게
        and type(p.get("headcount")) is int
    )


METHODS = {"ChooseLodging": (lodging_params, choose_lodging)}
# endregion


# region: call
def call(req):
    """요청 객체 하나 → 응답 객체. 알림(id 없음)이면 None."""
    if (
        not isinstance(req, dict)
        or req.get("jsonrpc") != "2.0"
        or not isinstance(req.get("method"), str)
    ):
        return error(-32600, "Invalid Request")
    rid, name = req.get("id"), req["method"]
    if name not in METHODS:
        resp = error(-32601, "Method not found", rid)
    elif not METHODS[name][0](req.get("params")):
        resp = error(-32602, "Invalid params", rid)
    else:
        try:
            result = METHODS[name][1](req["params"])
            resp = {"jsonrpc": "2.0", "id": rid, "result": result}
        # 메서드 안에서 터진 실패는 -32603
        except (ValueError, KeyError, TypeError):
            resp = error(-32603, "Internal error", rid)
    if "id" not in req:
        print(f"{name} 알림 → 응답 안 함", flush=True)
        return None
    outcome = resp["error"]["code"] if "error" in resp else "result"
    print(f"{name} id={json.dumps(rid)} → {outcome}", flush=True)
    return resp


# endregion


# region: handle
def handle(body):
    """HTTP 본문 → 응답(객체·배열) 또는 None(보낼 것이 없음)."""
    try:
        msg = json.loads(body)
    except ValueError:
        return error(-32700, "Parse error")
    if not isinstance(msg, list):
        return call(msg)
    if not msg:  # 빈 배치는 그 자체가 틀린 요청
        return error(-32600, "Invalid Request")
    out = [r for r in map(call, msg) if r is not None]
    return out or None  # 전부 알림이면 빈 배열이 아니라 무응답


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        resp = handle(self.rfile.read(n))
        if resp is None:
            self.send_response_only(204)  # 본문 없음
            self.end_headers()
            return
        data = json.dumps(resp, ensure_ascii=False).encode()
        self.send_response_only(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


# endregion


print(f"JSON-RPC 서버(py): 127.0.0.1:{args.port}", flush=True)
HTTPServer(("127.0.0.1", args.port), Handler).serve_forever()
# @ norun
