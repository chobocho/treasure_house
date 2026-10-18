# 완성 숙소·식사 에이전트(agents/)의 카드와 실행기를 그대로 빌려
# gRPC 문 하나로 띄운다. 카드는 여전히 HTTP 로 내준다.
#   python 13/grpc_agent.py lodging --port P --grpc-port G
#       [--grpc-url U]
#   python 13/grpc_agent.py catering … [--step-ms N]
import argparse
import asyncio

import grpc
import uvicorn
from a2a.server.request_handlers import (
    DefaultRequestHandler,
    GrpcHandler,
)
from a2a.server.routes import create_agent_card_routes
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import a2a_pb2_grpc
from starlette.applications import Starlette

from agents import catering, lodging

ap = argparse.ArgumentParser()
ap.add_argument("agent", choices=["lodging", "catering"])
ap.add_argument("--port", type=int, required=True, help="카드(HTTP)")
ap.add_argument("--grpc-port", type=int, required=True)
ap.add_argument("--grpc-url", help="카드에 적을 gRPC 주소")
ap.add_argument("--step-ms", type=int, default=100)
args = ap.parse_args()
target = args.grpc_url or f"127.0.0.1:{args.grpc_port}"
if args.agent == "lodging":
    card, executor = lodging.card(target), lodging.LodgingExecutor()
else:
    card = catering.card(target)
    executor = catering.CateringExecutor(args.step_ms)


# region: mount
async def main():
    # 카드의 문 하나를 GRPC 로 — 주소는 "호스트:포트"(스킴 없음)
    card.supported_interfaces[0].protocol_binding = "GRPC"
    handler = DefaultRequestHandler(
        agent_executor=executor,
        task_store=InMemoryTaskStore(),
        agent_card=card,
    )
    server = grpc.aio.server()
    a2a_pb2_grpc.add_A2AServiceServicer_to_server(
        GrpcHandler(handler), server
    )
    server.add_insecure_port(f"127.0.0.1:{args.grpc_port}")
    await server.start()
    # 발견은 바인딩과 따로 — 카드는 HTTP 의 잘 알려진 경로에
    app = Starlette(routes=create_agent_card_routes(card))
    http = uvicorn.Config(app, port=args.port, log_level="warning")
    await uvicorn.Server(http).serve()


# endregion
asyncio.run(main())
# @ norun
