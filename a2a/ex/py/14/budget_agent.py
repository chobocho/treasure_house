# 이 책의 예산 확장(budget/v1)을 완성 숙소 에이전트에 씌운다.
# agents/lodging.py 는 고치지 않는다 — 카드에 확장을 하나 적고,
# 실행기를 감싸 아티팩트에 예산 판정을 덧붙인다.
#   python 14/budget_agent.py --port P [--url U] [--required]
import argparse

from a2a.helpers import get_data_parts
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.types import AgentExtension, TaskArtifactUpdateEvent
from a2a.utils.errors import (
    ExtensionSupportRequiredError,
    InvalidParamsError,
)
from google.protobuf.json_format import MessageToDict

from agents import common, lodging

URI = "https://treasure-house.example/a2a/ext/budget/v1"


# region: declare
def declare(card, required):
    """카드의 capabilities.extensions 에 예산 확장을 적는다."""
    ext = AgentExtension(
        uri=URI,
        description="예산 상한(원)을 받아 견적과 견줍니다.",
        required=required,
        params={"currency": "KRW"},
    )
    card.capabilities.extensions.append(ext)


# endregion


# region: queue
class Marked(EventQueue):
    """지나가는 아티팩트에 예산 판정을 덧붙이는 큐(감싸기)."""

    def __init__(self, inner: EventQueue, limit):
        self.inner, self.limit = inner, limit

    async def enqueue_event(self, event):
        if isinstance(event, TaskArtifactUpdateEvent):
            art = event.artifact
            total = get_data_parts(art.parts)[0]["total"]
            art.extensions.append(URI)
            within = total <= self.limit
            art.metadata.update(
                {URI: {"limit": self.limit, "within": within}}
            )
        await self.inner.enqueue_event(event)


# endregion


# region: executor
class BudgetExecutor(AgentExecutor):
    def __init__(self, inner: AgentExecutor, required: bool):
        self.inner, self.required = inner, required

    async def execute(self, ctx: RequestContext, queue: EventQueue):
        # 요청의 A2A-Extensions 머리글을 SDK 가 쉼표로 나눠 둔 것
        if URI not in ctx.requested_extensions:
            if self.required:  # 파이썬 SDK 는 검사해 주지 않는다
                raise ExtensionSupportRequiredError(f"{URI} 필요")
            return await self.inner.execute(ctx, queue)
        meta = MessageToDict(ctx.message.metadata).get(URI, {})
        if "limit" not in meta:
            raise InvalidParamsError("예산 확장: limit 이 없습니다")
        await self.inner.execute(ctx, Marked(queue, meta["limit"]))

    async def cancel(self, ctx: RequestContext, queue: EventQueue):
        await self.inner.cancel(ctx, queue)


# endregion

# region: serve
ap = argparse.ArgumentParser()
ap.add_argument("--port", type=int, required=True)
ap.add_argument("--url")
ap.add_argument("--required", action="store_true")
args = ap.parse_args()
card = lodging.card(args.url or f"http://127.0.0.1:{args.port}/")
declare(card, args.required)
inner = lodging.LodgingExecutor()
executor = BudgetExecutor(inner, args.required)
common.serve(card, executor, args.port)
# endregion
# @ norun
