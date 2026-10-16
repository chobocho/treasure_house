# 숙소 에이전트(agents/lodging.py)를 그대로 쓰되, 카드의 인터페이스
# 목록을 바꿔 띄운다. 클라이언트가 목록에서 무엇을 고르는지 보는 실험.
#   --rest      HTTP+JSON 문(/rest)을 열고 목록 맨 앞에 적는다
#   --tenant T  모든 인터페이스에 tenant 를 적는다
import argparse

import uvicorn
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import (
    create_agent_card_routes,
    create_jsonrpc_routes,
    create_rest_routes,
)
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentInterface
from starlette.applications import Starlette

from agents.lodging import LodgingExecutor, card

ap = argparse.ArgumentParser()
ap.add_argument("--port", type=int, required=True)
ap.add_argument("--url", help="카드에 적을 바깥 주소")
ap.add_argument("--rest", action="store_true")
ap.add_argument("--tenant", default="")
args = ap.parse_args()
url = args.url or f"http://127.0.0.1:{args.port}/"

# region: doors
doors = [("JSONRPC", url)]
if args.rest:
    doors.insert(0, ("HTTP+JSON", url + "rest"))
c = card(url)
del c.supported_interfaces[:]
for binding, u in doors:
    c.supported_interfaces.append(
        AgentInterface(
            url=u,
            protocol_binding=binding,
            tenant=args.tenant,
            protocol_version="1.0",
        )
    )
# endregion
handler = DefaultRequestHandler(
    agent_executor=LodgingExecutor(),
    task_store=InMemoryTaskStore(),
    agent_card=c,
)
routes = [
    *create_agent_card_routes(c),
    *create_jsonrpc_routes(handler, "/"),
]
if args.rest:
    routes += create_rest_routes(handler, path_prefix="/rest")
app = Starlette(routes=routes)
uvicorn.run(app, host="127.0.0.1", port=args.port, log_level="warning")
# @ norun
