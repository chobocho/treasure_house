# 요청의 HTTP 정보는 실행기에 어떻게 닿나 —
# ServerCallContext 를 되돌려 준다.
#   python 07/headers.py --port P
import argparse

import uvicorn
from a2a.helpers import new_message, new_text_part
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import create_jsonrpc_routes
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import UnsupportedOperationError
from starlette.applications import Starlette
from step1_echo import card


# region: executor
class WhoExecutor(AgentExecutor):
    async def execute(self, ctx: RequestContext, queue: EventQueue):
        call = ctx.call_context  # 경로가 HTTP 요청에서 만든 것
        headers = call.state["headers"]  # 헤더 이름은 소문자
        said = [
            f"user_name={call.user.user_name!r}",
            f"인증됨={call.user.is_authenticated}",
            f"a2a-version={headers.get('a2a-version')}",
            f"x-workshop-team={headers.get('x-workshop-team')}",
            f"확장={sorted(ctx.requested_extensions)}",
        ]
        parts = [new_text_part(s) for s in said]
        reply = new_message(parts, context_id=ctx.context_id)
        await queue.enqueue_event(reply)

    async def cancel(self, ctx: RequestContext, queue: EventQueue):
        raise UnsupportedOperationError


# endregion

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--port", type=int, required=True)
    args = p.parse_args()
    handler = DefaultRequestHandler(
        agent_executor=WhoExecutor(),
        task_store=InMemoryTaskStore(),
        agent_card=card(f"http://127.0.0.1:{args.port}/"),
    )
    app = Starlette(routes=create_jsonrpc_routes(handler, "/"))
    uvicorn.run(
        app, host="127.0.0.1", port=args.port, log_level="warning"
    )
# @ norun
