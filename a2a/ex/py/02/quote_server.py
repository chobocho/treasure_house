# 숙소 견적을 내주는 작은 HTTP 서버 — 표준 라이브러리만.
# 아직 A2A 도 JSON-RPC 도 아니다. HTTP 요청·응답의 모양만 본다.
import argparse
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

from workshop.domain import choose_lodging

ap = argparse.ArgumentParser()
ap.add_argument("--port", type=int, required=True)
args = ap.parse_args()

TEXT = "text/plain; charset=utf-8"


# region: handler
class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def reply(self, status, ctype, body, extra=()):
        data = body.encode("utf-8")
        # send_response 는 Date·Server 를 덧붙인다. 시각이 캡처를
        # 흔들지 않게 상태 줄만 쓰는 send_response_only 를 쓴다.
        self.send_response_only(status)
        self.send_header("Content-Type", ctype)
        # 길이는 글자 수가 아니라 UTF-8 바이트 수다.
        self.send_header("Content-Length", str(len(data)))
        for k, v in extra:
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(data)
        # 기본 접속 기록에는 시각이 붙는다 — 요청 줄과 상태만 찍는다.
        print(f'"{self.requestline}" {status}', flush=True)

    def do_GET(self):
        if self.path == "/quote":  # 경로는 있지만 GET 은 안 받는다
            self.reply(
                405, TEXT, "POST 만 받습니다\n", [("Allow", "POST")]
            )
        else:
            self.reply(404, TEXT, "없는 경로입니다\n")

    def do_POST(self):
        # 본문은 먼저 다 읽는다 — 남기면 다음 요청으로 읽힌다.
        n = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(n)
        if self.path != "/quote":
            return self.reply(404, TEXT, "없는 경로입니다\n")
        try:
            req = json.loads(raw)
        except ValueError:
            return self.reply(400, TEXT, "JSON 이 아닙니다\n")
        body = json.dumps(choose_lodging(req), ensure_ascii=False)
        self.reply(200, "application/json", body)


# endregion


print(f"견적 서버: 127.0.0.1:{args.port}", flush=True)
HTTPServer(("127.0.0.1", args.port), Handler).serve_forever()
# @ norun
