"""푸시 알림을 받아 찍기만 하는 웹훅 수신기(표준 라이브러리만).

에이전트가 POST 로 보내는 몸통(StreamResponse 모양의 JSON)과 토큰
헤더를 한 줄 요약으로 찍는다. 받은 순서대로 번호를 붙인다.
"""

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Lock

COUNT = 0
LOCK = Lock()


# region: summary
def summary(body):
    """{'statusUpdate': {...}} → 'statusUpdate TASK_STATE_WORKING …'"""
    (kind, event), *_ = body.items()
    if kind == "statusUpdate":
        st = event["status"]
        parts = st.get("message", {}).get("parts", [])
        text = " ".join(p["text"] for p in parts if "text" in p)
        return f"{kind} {st['state']} {text}".rstrip()
    if kind == "artifactUpdate":
        return f"{kind} {event['artifact'].get('name', '')}"
    if kind == "task":
        return f"{kind} {event['status']['state']}"
    return kind


# endregion


# region: hook
class Hook(BaseHTTPRequestHandler):
    def do_POST(self):
        global COUNT
        size = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(size))
        token = self.headers.get("X-A2A-Notification-Token", "-")
        with LOCK:
            COUNT += 1
            print(f"#{COUNT} token={token} {summary(body)}", flush=True)
        self.send_response(204)
        self.end_headers()

    def log_message(self, *args):  # 접속 기록은 끈다
        pass


# endregion


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--port", type=int, required=True)
    port = p.parse_args().port
    ThreadingHTTPServer(("127.0.0.1", port), Hook).serve_forever()
