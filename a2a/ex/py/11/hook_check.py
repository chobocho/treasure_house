# 토큰을 확인하는 웹훅 수신기 — 설정에 적어 준 토큰이 아니면 401.
# agents/webhook.py 는 받은 것을 찍기만 한다. 이것은 문을 지킨다.
#   python 11/hook_check.py --port P --token T
import argparse
import hmac
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

TOKEN = ""


class Hook(BaseHTTPRequestHandler):
    # region: check
    def do_POST(self):
        size = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(size))
        got = self.headers.get("X-A2A-Notification-Token", "")
        # == 대신 compare_digest — 걸린 시간으로 토큰을 짐작하지 못하게
        if not hmac.compare_digest(got.encode(), TOKEN.encode()):
            print(f"거절 401: token={got or '-'}", flush=True)
            self.send_response(401)
            self.end_headers()
            return
        ((kind, _),) = body.items()
        print(f"통과 204: {kind}", flush=True)
        self.send_response(204)
        self.end_headers()

    # endregion

    def log_message(self, *args):  # 접속 기록은 끈다
        pass


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--port", type=int, required=True)
    p.add_argument("--token", required=True)
    a = p.parse_args()
    TOKEN = a.token
    ThreadingHTTPServer(("127.0.0.1", a.port), Hook).serve_forever()
# @ norun
