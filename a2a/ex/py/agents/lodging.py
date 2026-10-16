"""숙소 에이전트 — 날짜·박 수·인원을 받아 가장 싼 숙소를 고른다.

보여 주는 것: 막는(blocking) SendMessage → Task, DataPart 입출력,
INPUT_REQUIRED 로 되묻기(같은 taskId 로 이어 말하기), REJECTED.
"""

from a2a.helpers.proto_helpers import (
    get_message_text,
    new_data_part,
    new_text_part,
)
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import AgentCapabilities, AgentCard, AgentSkill

from agents.common import (
    PROVIDER,
    as_ints,
    begin,
    data_of,
    jsonrpc_interface,
    parse_args,
    serve,
)
from workshop import domain

# 빠진 항목을 하나씩 되묻는다. 순서가 곧 묻는 순서다.
QUESTIONS = {
    "date": "날짜는 언제입니까? (예: 2026-10-30)",
    "nights": "며칠 묵습니까? (예: 1박)",
    "headcount": "인원은 몇 명입니까?",
}


def card(url):
    return AgentCard(
        name="보물상사 숙소 에이전트",
        description="날짜·박 수·인원으로 가장 싼 숙소를 고릅니다.",
        version="1.0.0",
        provider=PROVIDER,
        supported_interfaces=[jsonrpc_interface(url)],
        capabilities=AgentCapabilities(streaming=True),
        default_input_modes=["application/json", "text/plain"],
        default_output_modes=["application/json"],
        skills=[
            AgentSkill(
                id="find-lodging",
                name="숙소 찾기",
                description="워크숍 숙소를 고르고 견적을 냅니다.",
                tags=["lodging", "workshop"],
                examples=[
                    '{"date":"2026-10-30","nights":1,"headcount":30}'
                ],
            )
        ],
    )


def from_text(text):
    """되물음에 글로 답한 경우('30명')를 DataPart 처럼 바꾼다."""
    found = {}
    for key, rx in (
        ("date", domain.DATE),
        ("nights", domain.NIGHTS),
        ("headcount", domain.HEADCOUNT),
    ):
        m = rx.search(text)
        if m:
            found[key] = m.group(1)
    return found


class LodgingExecutor(AgentExecutor):
    async def execute(self, ctx: RequestContext, queue: EventQueue):
        task, up = await begin(ctx, queue)
        # 지금까지 들은 것 전부(이력 + 이번 메시지)를 합친다.
        heard = task.history  # begin() 이 이번 메시지까지 넣어 둔다
        req = data_of(*heard)
        for m in heard:
            req.update(from_text(get_message_text(m)))
        missing = [k for k in QUESTIONS if k not in req]
        if missing:
            ask = up.new_agent_message(
                [
                    new_text_part(QUESTIONS[missing[0]]),
                    new_data_part({"missing": missing}),
                ]
            )
            print(f"[숙소] 되묻기: {missing}", flush=True)
            await up.requires_input(ask)
            return
        quote = domain.choose_lodging(
            as_ints(req, "nights", "headcount")
        )
        if not quote["ok"]:
            print(f"[숙소] 거절: {quote['reason']}", flush=True)
            await up.reject(
                up.new_agent_message([new_text_part(quote["reason"])])
            )
            return
        summary = (
            f"{quote['venueName']} {quote['rooms']}실, "
            f"{quote['total']:,}원"
        )
        print(f"[숙소] 견적: {summary}", flush=True)
        await up.add_artifact(
            [new_data_part(quote), new_text_part(summary)],
            name="숙소 견적",
        )
        await up.complete()

    async def cancel(self, ctx: RequestContext, queue: EventQueue):
        task = ctx.current_task
        await TaskUpdater(queue, task.id, task.context_id).cancel()


if __name__ == "__main__":
    args = parse_args("보물상사 숙소 에이전트")
    serve(card(args.url), LodgingExecutor(), args.port)
