# 한 서버, 세 바인딩 — 완성 숙소 에이전트의 카드와 실행기를 빌려
# JSON-RPC(/)·HTTP+JSON(/rest)·gRPC(포트 G) 세 문을 한꺼번에 연다.
# 요청 처리기와 작업 저장소는 하나다. 어느 문으로 들어왔는지 한 줄씩
# 찍는다(카드 요청은 [카드]).
#   python 13/doors.py --port P --grpc-port G [--grpc-url U]
import argparse
import asyncio

import grpc
import uvicorn
from a2a.server.request_handlers import (
    DefaultRequestHandler,
    GrpcHandler,
)
from a2a.server.routes import (
    create_agent_card_routes,
    create_jsonrpc_routes,
    create_rest_routes,
)
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentInterface, a2a_pb2_grpc
from starlette.applications import Starlette

from agents import lodging

ap = argparse.ArgumentParser()
ap.add_argument("--port", type=int, required=True)
ap.add_argument("--grpc-port", type=int, required=True)
ap.add_argument(
    "--grpc-url", help="카드에 적을 gRPC 주소(기본: 붙는 곳)"
)
args = ap.parse_args()
http_url = f"http://127.0.0.1:{args.port}/"
grpc_url = args.grpc_url or f"127.0.0.1:{args.grpc_port}"


def door(path):
    if path.startswith("/.well-known/"):
        return "카드"
    return "HTTP+JSON" if path.startswith("/rest/") else "JSONRPC"


async def log_http(scope, receive, send, app):
    if scope["type"] == "http":
        print(
            f"[{door(scope['path'])}] {scope['method']} {scope['path']}"
        )
    await app(scope, receive, send)


class LogGrpc(grpc.aio.ServerInterceptor):
    async def intercept_service(self, cont, details):
        print(f"[GRPC] {details.method}")
        return await cont(details)


# region: mount
card = lodging.card(http_url)
# 카드에 세 문을 모두 적는다(§5.2 MUST) — 차례가 서버의 선호다
card.supported_interfaces.extend(
    [
        AgentInterface(
            url=http_url + "rest",
            protocol_binding="HTTP+JSON",
            protocol_version="1.0",
        ),
        AgentInterface(
            url=grpc_url,
            protocol_binding="GRPC",
            protocol_version="1.0",
        ),
    ]
)
handler = DefaultRequestHandler(
    agent_executor=lodging.LodgingExecutor(),
    task_store=InMemoryTaskStore(),
    agent_card=card,
)
app = Starlette(
    routes=[
        *create_agent_card_routes(card),
        *create_rest_routes(handler, path_prefix="/rest"),
        *create_jsonrpc_routes(handler, rpc_url="/"),
    ]
)
# endregion


async def main():
    # region: grpc
    server = grpc.aio.server(interceptors=[LogGrpc()])
    a2a_pb2_grpc.add_A2AServiceServicer_to_server(
        GrpcHandler(handler), server
    )
    server.add_insecure_port(f"127.0.0.1:{args.grpc_port}")
    await server.start()
    # endregion

    async def logged(scope, receive, send):
        await log_http(scope, receive, send, app)

    http = uvicorn.Config(logged, port=args.port, log_level="warning")
    await uvicorn.Server(http).serve()


asyncio.run(main())
# @ norun
