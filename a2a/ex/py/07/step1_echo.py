# 1단계 — 메아리 에이전트: 받은 글을 Message 하나로 돌려준다.
#   python 07/step1_echo.py --port P [--url U]
# 실행기(3장) → 요청 처리기(4장) → 서버(5장)를 한 파일에 담았다.
import argparse

import uvicorn
from a2a.helpers import new_text_message
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import (
    create_agent_card_routes,
    create_jsonrpc_routes,
)
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentInterface,
    AgentSkill,
    UnsupportedOperationError,
)
from starlette.applications import Starlette


# region: executor
class EchoExecutor(AgentExecutor):
    async def execute(self, ctx: RequestContext, queue: EventQueue):
        text = ctx.get_user_input()  # 글 파트를 모두 이은 것
        reply = new_text_message(
            f"받은 말: {text}", context_id=ctx.context_id
        )
        await queue.enqueue_event(reply)  # 이벤트는 이것 하나뿐

    async def cancel(self, ctx: RequestContext, queue: EventQueue):
        # Message 만 내는 에이전트에는 취소할 작업이 없다
        raise UnsupportedOperationError


# endregion


# region: card
def card(url):
    return AgentCard(
        name="보물상사 메아리 에이전트",
        description="받은 글을 그대로 돌려줍니다.",
        version="0.1.0",
        supported_interfaces=[
            AgentInterface(
                url=url,
                protocol_binding="JSONRPC",
                protocol_version="1.0",
            )
        ],
        capabilities=AgentCapabilities(),
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain"],
        skills=[
            AgentSkill(
                id="echo",
                name="메아리",
                description="받은 글을 돌려줍니다.",
                tags=["debug"],
            )
        ],
    )


# endregion


# region: serve
def main():
    p = argparse.ArgumentParser()
    p.add_argument("--port", type=int, required=True)
    p.add_argument("--url")  # 카드에 적을 바깥 주소
    args = p.parse_args()
    agent_card = card(args.url or f"http://127.0.0.1:{args.port}/")
    handler = DefaultRequestHandler(
        agent_executor=EchoExecutor(),
        task_store=InMemoryTaskStore(),
        agent_card=agent_card,
    )
    app = Starlette(
        routes=[
            *create_agent_card_routes(agent_card),
            *create_jsonrpc_routes(handler, "/"),
        ]
    )
    uvicorn.run(
        app, host="127.0.0.1", port=args.port, log_level="warning"
    )


# endregion

if __name__ == "__main__":
    main()
# @ norun
