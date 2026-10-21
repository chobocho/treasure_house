# 카드 대신 ETag 하나만 주고, 받은 요청의 캐시 관련 머리글을 찍는 서버.
# 클라이언트 라이브러리가 조건부 GET 에 무엇을 덧붙이는지 보려는 것.
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

SHOW = ("If-None-Match", "Cache-Control", "Pragma")


# region: handler
class Echo(BaseHTTPRequestHandler):
    def do_GET(self):
        got = [f"{h}: {self.headers.get(h, '-')}" for h in SHOW]
        print(" · ".join(got), flush=True)
        self.send_response(200)
        self.send_header("ETag", 'W/"echo"')
        self.send_header("Content-Length", "2")
        self.end_headers()
        self.wfile.write(b"{}")

    def log_message(self, *args):  # 기본 접속 기록(시각 포함)은 끈다
        pass


# endregion

HTTPServer(("127.0.0.1", int(sys.argv[1])), Echo).serve_forever()
# @ norun
