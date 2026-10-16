"""다섯 에이전트가 함께 쓰는 SDK 접착 코드.

업무 규칙은 workshop.domain 에 있고, 여기는 A2A 쪽 잔일만 한다:
명령줄 읽기, 카드의 공통 부분, DataPart 꺼내기, 서버 띄우기.
"""

import argparse

import uvicorn
from a2a.helpers.proto_helpers import get_data_parts
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import (
    create_agent_card_routes,
    create_jsonrpc_routes,
)
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentInterface, AgentProvider, Message
from starlette.applications import Starlette

PROVIDER = AgentProvider(
    organization="보물상사", url="https://treasure-house.example"
)


def parse_args(description, **extra):
    """--port 는 붙을 곳, --url 은 카드에 적을 바깥 주소.

    extra 는 에이전트마다 더 받는 정수 옵션: 이름=(설명, 기본값).
    """
    p = argparse.ArgumentParser(description=description)
    p.add_argument("--port", type=int, required=True)
    p.add_argument("--url", help="카드에 적을 주소(기본: 붙는 주소)")
    for name, (help_, default) in extra.items():
        flag = "--" + name.replace("_", "-")
        p.add_argument(flag, type=int, default=default, help=help_)
    args = p.parse_args()
    args.url = args.url or f"http://127.0.0.1:{args.port}/"
    return args


def jsonrpc_interface(url):
    return AgentInterface(
        url=url, protocol_binding="JSONRPC", protocol_version="1.0"
    )


def data_of(*messages: Message) -> dict:
    """메시지들의 DataPart 를 앞에서부터 차례로 덮어 합친다."""
    merged = {}
    for m in messages:
        for d in get_data_parts(m.parts):
            if isinstance(d, dict):
                merged.update(d)
    return merged


def as_ints(d: dict, *keys) -> dict:
    """JSON 숫자는 protobuf Value 를 거치며 실수(30.0)가 된다.

    업무 규칙은 정수를 기대하므로 여기서 되돌린다.
    """
    return {k: int(v) if k in keys else v for k, v in d.items()}


def serve(
    card, executor, port, *, routes=(), middleware=(), **handler_options
):
    """JSON-RPC 와 카드 경로를 단 Starlette 앱을 띄운다.

    routes·middleware 는 정산 에이전트처럼 경로(토큰 발급)나 인증
    검사를 더 다는 에이전트를 위한 것이다.
    """
    handler = DefaultRequestHandler(
        agent_executor=executor,
        task_store=InMemoryTaskStore(),
        agent_card=card,
        **handler_options,
    )
    app = Starlette(
        routes=[
            *routes,
            *create_agent_card_routes(card),
            *create_jsonrpc_routes(handler, "/"),
        ],
        middleware=list(middleware),
    )
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")
