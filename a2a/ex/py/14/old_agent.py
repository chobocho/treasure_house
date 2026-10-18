# 완성 숙소 에이전트를 v0.3 판 JSON-RPC 로도 받게 띄운다. 카드에는
# 판 0.3 문 하나만 적는다 — v0.3 만 아는 옛 에이전트의 흉내다(처리기
# 는 v1.0 요청도 받는다).
#   python 14/old_agent.py --port P [--url U]
import argparse

import uvicorn
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import (
    create_agent_card_routes,
    create_jsonrpc_routes,
)
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentInterface
from starlette.applications import Starlette

from agents import lodging

ap = argparse.ArgumentParser()
ap.add_argument("--port", type=int, required=True)
ap.add_argument("--url")
args = ap.parse_args()
url = args.url or f"http://127.0.0.1:{args.port}/"

# region: serve
card = lodging.card(url)
del card.supported_interfaces[:]  # 판 1.0 문을 지우고
old = AgentInterface(url=url, protocol_binding="JSONRPC")
old.protocol_version = "0.3"  # 판 0.3 문 하나만
card.supported_interfaces.append(old)
handler = DefaultRequestHandler(
    agent_executor=lodging.LodgingExecutor(),
    task_store=InMemoryTaskStore(),
    agent_card=card,
)
routes = create_agent_card_routes(card)  # 카드에 v0.3 칸을 섞는다
routes += create_jsonrpc_routes(handler, "/", enable_v0_3_compat=True)
# endregion
app = Starlette(routes=routes)
uvicorn.run(app, host="127.0.0.1", port=args.port, log_level="warning")
# @ norun
