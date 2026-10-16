# SSE 서버 — http.server 만으로. 식단을 짜며 끼니마다 이벤트 하나를
# 흘려 보내고, 마지막에 합계를 보낸 뒤 연결을 닫는다.
import argparse
import json
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

from workshop.domain import plan_meals

ap = argparse.ArgumentParser()
ap.add_argument("--port", type=int, required=True)
args = ap.parse_args()


def events(req):
    """이벤트로 보낼 dict 들 — 끼니마다 하나, 끝에 합계."""
    plan = plan_meals(req)
    if not plan["ok"]:
        yield plan
        return
    for s in plan["slots"]:
        yield {
            "slot": s["slot"],
            "regular": s["regular"]["name"],
            "vegetarian": s["vegetarian"]["name"],
        }
    yield {"total": plan["total"]}


# region: stream
class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        req = json.loads(self.rfile.read(n))
        self.send_response_only(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        # 길이를 모르므로 닫는 것으로 끝을 알린다
        self.send_header("Connection", "close")
        self.end_headers()
        count = 0
        for ev in events(req):
            data = json.dumps(
                ev, ensure_ascii=False, separators=(",", ":")
            )
            # 이벤트 하나 = "data: …" 줄 + 빈 줄
            self.wfile.write(f"data: {data}\n\n".encode())
            self.wfile.flush()  # 모아 두지 말고 지금 보낸다
            count += 1
            time.sleep(0.05)  # 식단 짜는 시간인 셈
        print(f"이벤트 {count}개를 보내고 닫음", flush=True)


# endregion

print(f"SSE 서버(py): 127.0.0.1:{args.port}", flush=True)
HTTPServer(("127.0.0.1", args.port), Handler).serve_forever()
# @ norun
