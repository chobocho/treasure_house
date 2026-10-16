# 카드만 내주는 서버 — 표준 라이브러리만. SDK 는 아직 없다.
# 카드는 정해진 경로에 놓인 JSON 문서 한 장일 뿐이다.
import argparse
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

ap = argparse.ArgumentParser()
ap.add_argument("--port", type=int, required=True)
ap.add_argument("--url", help="카드에 적을 바깥 주소")
args = ap.parse_args()
url = args.url or f"http://127.0.0.1:{args.port}/"

# region: card
CARD = {
    "name": "보물상사 숙소 에이전트",
    "description": "날짜·박 수·인원으로 가장 싼 숙소를 고릅니다.",
    "supportedInterfaces": [
        {
            "url": url,
            "protocolBinding": "JSONRPC",
            "protocolVersion": "1.0",
        }
    ],
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
        }
    ],
}
# endregion


# region: handler
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/.well-known/agent-card.json":
            status, ctype = 200, "application/json"
            body = json.dumps(CARD, ensure_ascii=False)
        else:
            status, ctype = 404, "text/plain; charset=utf-8"
            body = "없는 경로입니다\n"
        data = body.encode("utf-8")
        # send_response 는 시각이 찍힌 접속 기록을 남긴다 — 상태 줄만
        self.send_response_only(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


# endregion

HTTPServer(("127.0.0.1", args.port), Handler).serve_forever()
# @ norun
