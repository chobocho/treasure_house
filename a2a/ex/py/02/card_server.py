# 가장 작은 Agent Card 서버 — 표준 라이브러리만으로 카드 한 장을 내준다.
# (환경 확인 때 SDK 로 띄운 hello 에이전트의 카드를 맨손으로 옮겼다.)
import argparse
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

ap = argparse.ArgumentParser()
ap.add_argument("--port", type=int, required=True)
ap.add_argument("--url", required=True)  # 바깥에서 닿는 주소
args = ap.parse_args()

# region: card
CARD = {
    "name": "py-hello",
    "description": "hello",
    "version": "1.0.0",
    "supportedInterfaces": [
        {
            "url": args.url,
            "protocolBinding": "JSONRPC",
            "protocolVersion": "1.0",
        }
    ],
    "capabilities": {"streaming": True},
    "defaultInputModes": ["text/plain"],
    "defaultOutputModes": ["text/plain"],
    "skills": [
        {
            "id": "hello",
            "name": "hello",
            "description": "says hello",
            "tags": ["demo"],
        }
    ],
}
# endregion


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path != "/.well-known/agent-card.json":
            self.send_error(404)
            return
        body = json.dumps(CARD, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *a):
        # 기본 접속 기록에는 시각이 붙는다 — 요청 줄과 상태만 찍는다.
        print(fmt % a, flush=True)


print(f"카드 서버: 127.0.0.1:{args.port}", flush=True)
HTTPServer(("127.0.0.1", args.port), Handler).serve_forever()
# @ norun
