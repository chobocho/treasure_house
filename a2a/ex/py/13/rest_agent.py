# 완성 숙소·식사 에이전트(agents/)의 카드와 실행기를 그대로 빌려
# HTTP+JSON(REST) 문 하나로 띄운다. 바뀌는 것은 바인딩뿐이다.
#   python 13/rest_agent.py lodging --port P [--url U]
#   python 13/rest_agent.py catering --port P [--step-ms N]
import argparse

import uvicorn
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import (
    create_agent_card_routes,
    create_rest_routes,
)
from a2a.server.tasks import InMemoryTaskStore
from starlette.applications import Starlette

from agents import catering, lodging

ap = argparse.ArgumentParser()
ap.add_argument("agent", choices=["lodging", "catering"])
ap.add_argument("--port", type=int, required=True)
ap.add_argument("--url", help="카드에 적을 바깥 주소")
ap.add_argument("--step-ms", type=int, default=100)
args = ap.parse_args()
url = args.url or f"http://127.0.0.1:{args.port}/"
if args.agent == "lodging":
    card, executor = lodging.card(url), lodging.LodgingExecutor()
else:
    card = catering.card(url)
    executor = catering.CateringExecutor(args.step_ms)

# region: mount
# 카드의 문 하나를 HTTP+JSON 으로 바꿔 적는다(주소는 그대로).
card.supported_interfaces[0].protocol_binding = "HTTP+JSON"
handler = DefaultRequestHandler(
    agent_executor=executor,
    task_store=InMemoryTaskStore(),
    agent_card=card,
)
app = Starlette(
    routes=[
        *create_agent_card_routes(card),
        # JSON-RPC 의 create_jsonrpc_routes 자리에 이 한 줄
        *create_rest_routes(handler),
    ]
)
# endregion
uvicorn.run(app, host="127.0.0.1", port=args.port, log_level="warning")
# @ norun
