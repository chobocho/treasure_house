"""교통 에이전트에 카드 캐시 머리글과 본문 한도를 단다.

    python 17/bus_ops.py --port P [--step-ms N] [--cache-age 초]
                         [--limit 바이트]

실행기·카드는 agents/bus.py 의 것(가져다 쓴다). 0 이면 끈다.
"""

import argparse
import json

import uvicorn
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import (
    create_agent_card_routes,
    create_jsonrpc_routes,
)
from a2a.server.tasks import InMemoryTaskStore
from starlette.applications import Starlette

from agents.bus import BusExecutor, card


# region: limit
class BodyLimit:
    """Content-Length 가 한도를 넘는 요청을 SDK 앞에서 413 으로.

    본문은 읽지 않는다. 길이를 밝히지 않는 조각 전송(chunked)은
    receive 를 감싸 세어야 하는데, 이 예제는 하지 않는다.
    """

    def __init__(self, app, limit):
        self.app, self.limit = app, limit

    async def __call__(self, scope, receive, send):
        size = dict(scope.get("headers", [])).get(b"content-length")
        if self.limit and size and int(size) > self.limit:
            # 스펙에 크기 초과 오류는 없다 — Invalid Request 를 싣는다
            err = {"code": -32600, "message": "요청 본문이 너무 큽니다"}
            body = {"jsonrpc": "2.0", "id": None, "error": err}
            await send(
                {
                    "type": "http.response.start",
                    "status": 413,
                    "headers": [(b"content-type", b"application/json")],
                }
            )
            raw = json.dumps(body, ensure_ascii=False).encode()
            await send({"type": "http.response.body", "body": raw})
            return
        await self.app(scope, receive, send)


# endregion

p = argparse.ArgumentParser(description="캐시·한도를 단 교통 에이전트")
p.add_argument("--port", type=int, required=True)
p.add_argument("--step-ms", type=int, default=300)
p.add_argument("--cache-age", type=int, default=0)
p.add_argument("--limit", type=int, default=0)
args = p.parse_args()
url = f"http://127.0.0.1:{args.port}/"
handler = DefaultRequestHandler(
    agent_executor=BusExecutor(args.step_ms),
    task_store=InMemoryTaskStore(),
    agent_card=card(url),
)
# region: card
cache = f"public, max-age={args.cache_age}" if args.cache_age else None
app = Starlette(
    routes=[
        # SDK 의 카드 경로는 ETag 을 늘 달고, Cache-Control 은 줄 때만
        *create_agent_card_routes(card(url), cache_control=cache),
        *create_jsonrpc_routes(handler, "/"),
    ]
)
app = BodyLimit(app, args.limit)  # 앱 맨 바깥에
# endregion
uvicorn.run(app, host="127.0.0.1", port=args.port, log_level="warning")
# @ norun
