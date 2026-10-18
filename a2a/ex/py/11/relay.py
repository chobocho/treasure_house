# 시험 쪽 웹훅 중계기 — 에이전트가 보낸 푸시를 (있으면) 진짜 수신기에
# 넘기고, 다 넘긴 것을 작업별로 적어 둔다. 시험 클라이언트는
#   GET /wait?task=ID&n=N[&token=T]
#       그 작업의 끝 알림 N건(토큰 T 로 온 것만)이 지나갈 때까지
#   GET /seen               지금까지 온 것 전부(기다리지 않는다)
# 로 묻는다 — 몇 초 쉬어 보는 대신, 일어난 일에 맞춰 기다리려는 것이다.
#   python 11/relay.py --port P [--to http://127.0.0.1:Q/]
# POST /Q 처럼 경로에 포트를 적으면 127.0.0.1:Q 로 넘긴다(수신기 여럿).
import argparse
import json
import threading
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

END = ("COMPLETED", "FAILED", "CANCELED", "REJECTED")
PASS = ("Content-Type", "X-A2A-Notification-Token", "Authorization")
SEEN = {}  # 작업 id → [{"what", "token", "end", "code"}, …]
CV = threading.Condition()


def summary(body, token):
    """StreamResponse 하나 → 작업 id 와 한 줄 기록."""
    ((kind, ev),) = body.items()
    tid = ev["id"] if kind == "task" else ev.get("taskId", "")
    state = ev["status"]["state"][11:] if "status" in ev else ""
    what = f"{kind} {state}".rstrip()
    return tid, {"what": what, "token": token, "end": state in END}


def forward(to, raw, headers):
    """진짜 수신기에 그대로 넘기고 그 상태 코드를 돌려준다."""
    if not to:
        return 204
    head = {h: headers[h] for h in PASS if h in headers}
    try:
        req = urllib.request.Request(to, raw, head)
        with urllib.request.urlopen(req) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code


class Relay(BaseHTTPRequestHandler):
    # region: relay
    def do_POST(self):
        raw = self.rfile.read(int(self.headers["Content-Length"]))
        to = self.server.to
        if self.path[1:].isdigit():
            to = f"http://127.0.0.1:{self.path[1:]}/"
        code = forward(to, raw, self.headers)
        token = self.headers.get("X-A2A-Notification-Token", "-")
        tid, rec = summary(json.loads(raw), token)
        rec["code"] = code
        with CV:
            SEEN.setdefault(tid, []).append(rec)
            CV.notify_all()
        self.send_response(code)
        self.end_headers()

    def do_GET(self):
        q = parse_qs(urlparse(self.path).query)
        tid, n = q.get("task", [""])[0], int(q.get("n", ["1"])[0])
        tok = q.get("token", [None])[0]

        def done():
            ends = [r for r in SEEN.get(tid, []) if r["end"]]
            return (
                len([r for r in ends if tok in (None, r["token"])]) >= n
            )

        with CV:
            if tid:
                CV.wait_for(done, timeout=20)
            got = SEEN.get(tid, []) if tid else SEEN
            body = json.dumps(got, ensure_ascii=False).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)

    # endregion

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--port", type=int, required=True)
    p.add_argument("--to", default="")
    a = p.parse_args()
    srv = ThreadingHTTPServer(("127.0.0.1", a.port), Relay)
    srv.to = a.to
    srv.serve_forever()
# @ norun
