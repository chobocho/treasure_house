# 2단계 — 견적 에이전트: DataPart 를 받아 Task 로 일하고
# 아티팩트를 낸다.
#   python 07/step2_task.py --port P [--url U] [--path /a2a]
# 1단계와 다른 것은 실행기와 카드, 그리고 JSON-RPC 를 다는 경로다.
import argparse

import uvicorn
from a2a.helpers import (
    get_data_parts,
    new_data_part,
    new_task_from_user_message,
    new_text_part,
)
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import (
    create_agent_card_routes,
    create_jsonrpc_routes,
)
from a2a.server.tasks import InMemoryTaskStore, TaskUpdater
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentInterface,
    AgentSkill,
)
from starlette.applications import Starlette

from workshop import domain


def request_of(message):
    """DataPart 들을 합치고, 수는 int 로 되돌린다(Value 는 실수)."""
    req = {}
    for d in get_data_parts(message.parts):
        req.update(d)
    for k in ("nights", "headcount"):
        if k in req:
            req[k] = int(req[k])
    return req


# region: executor
class QuoteExecutor(AgentExecutor):
    async def execute(self, ctx: RequestContext, queue: EventQueue):
        task = new_task_from_user_message(ctx.message)
        await queue.enqueue_event(task)  # ① Task 를 먼저(SUBMITTED)
        up = TaskUpdater(queue, task.id, task.context_id)
        await up.start_work()  # ② WORKING
        quote = domain.choose_lodging(request_of(ctx.message))
        if not quote["ok"]:  # ③ 거절 — 까닭을 상태 메시지로
            reason = new_text_part(quote["reason"])
            await up.reject(up.new_agent_message([reason]))
            return
        # ③ 견적은 아티팩트로, 그다음 끝
        await up.add_artifact([new_data_part(quote)], name="숙소 견적")
        await up.complete()

    async def cancel(self, ctx: RequestContext, queue: EventQueue):
        task = ctx.current_task
        await TaskUpdater(queue, task.id, task.context_id).cancel()


# endregion


def card(url):
    return AgentCard(
        name="보물상사 견적 에이전트",
        description="날짜·박 수·인원으로 숙소 견적을 냅니다.",
        version="0.2.0",
        supported_interfaces=[
            AgentInterface(
                url=url,
                protocol_binding="JSONRPC",
                protocol_version="1.0",
            )
        ],
        capabilities=AgentCapabilities(),
        default_input_modes=["application/json"],
        default_output_modes=["application/json"],
        skills=[
            AgentSkill(
                id="quote-lodging",
                name="숙소 견적",
                description="숙소를 고르고 견적을 냅니다.",
                tags=["lodging"],
            )
        ],
    )


# region: serve
def main():
    p = argparse.ArgumentParser()
    p.add_argument("--port", type=int, required=True)
    p.add_argument("--url")
    p.add_argument("--path", default="/")  # JSON-RPC 를 달 경로
    args = p.parse_args()
    base = f"http://127.0.0.1:{args.port}"
    agent_card = card(args.url or base + args.path)
    handler = DefaultRequestHandler(
        agent_executor=QuoteExecutor(),
        task_store=InMemoryTaskStore(),
        agent_card=agent_card,
    )
    routes = create_agent_card_routes(agent_card)
    routes += create_jsonrpc_routes(handler, args.path)
    app = Starlette(routes=routes)
    uvicorn.run(
        app, host="127.0.0.1", port=args.port, log_level="warning"
    )


# endregion

if __name__ == "__main__":
    main()
# @ norun
