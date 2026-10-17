"""식사 에이전트 — 끼니마다 메뉴를 골라 스트리밍으로 알려 준다.

보여 주는 것: SendStreamingMessage(SSE), 끼니마다 WORKING 상태 갱신,
식단표 아티팩트를 청크로 이어 붙이기(append·lastChunk), 파일 파트
(menu.md, raw)와 데이터 파트(견적)를 함께 돌려주기.
"""

import asyncio

from a2a.helpers.proto_helpers import (
    new_data_part,
    new_raw_part,
    new_text_part,
)
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
    TaskState,
)

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

# 끼니 이름표. 슬롯 이름(day1-dinner)을 사람이 읽는 말로 바꾼다.
KIND = {"dinner": "저녁", "breakfast": "아침", "lunch": "점심"}


def card(url):
    return AgentCard(
        name="보물상사 식사 에이전트",
        description="박 수·인원·채식 인원으로 끼니별 식단을 짭니다.",
        version="1.0.0",
        provider=PROVIDER,
        supported_interfaces=[jsonrpc_interface(url)],
        capabilities=AgentCapabilities(streaming=True),
        default_input_modes=["application/json"],
        default_output_modes=["application/json", "text/markdown"],
        skills=[
            AgentSkill(
                id="plan-meals",
                name="식단 짜기",
                description="끼니마다 일반식·채식 메뉴를 고릅니다.",
                tags=["meals", "workshop"],
                examples=[
                    '{"nights":1,"headcount":30,"vegetarians":2}'
                ],
            )
        ],
    )


def label(slot):
    """day1-dinner → 1일차 저녁"""
    day, kind = slot.split("-")
    return f"{day.removeprefix('day')}일차 {KIND[kind]}"


def line(row):
    """식단표의 한 줄: 1일차 저녁: 한정식 28명, 버섯 전골 2명"""
    picks = [
        f"{c['name']} {c['count']}명"
        for c in (row["regular"], row["vegetarian"])
        if c is not None
    ]
    return f"{label(row['slot'])}: {', '.join(picks)}"


# region: executor
class CateringExecutor(AgentExecutor):
    def __init__(self, step_ms):
        self.step = step_ms / 1000  # 끼니 사이 쉬는 시간(보여 주기용)

    async def execute(self, ctx: RequestContext, queue: EventQueue):
        _, up = await begin(ctx, queue)
        req = as_ints(
            data_of(ctx.message), "nights", "headcount", "vegetarians"
        )
        req.setdefault("vegetarians", 0)
        plan = domain.plan_meals(req)
        if not plan["ok"]:
            print(f"[식사] 거절: {plan['reason']}", flush=True)
            await up.reject(
                up.new_agent_message([new_text_part(plan["reason"])])
            )
            return
        # endregion
        # region: stream
        rows = plan["slots"]
        for i, row in enumerate(rows, 1):
            await asyncio.sleep(self.step)
            note = f"식단 짜는 중 {i}/{len(rows)}"
            await up.update_status(
                TaskState.TASK_STATE_WORKING,
                up.new_agent_message([new_text_part(note)]),
            )
            # region: chunk
            # 같은 artifactId 로 한 줄씩 이어 붙인다.
            await up.add_artifact(
                [new_text_part(line(row) + "\n")],
                artifact_id="meal-plan",
                name="식단표",
                append=i > 1,
                last_chunk=i == len(rows),
            )
            # endregion
        # endregion
        # region: finish
        menu = "# 식단표\n\n" + "".join(f"- {line(r)}\n" for r in rows)
        await up.add_artifact(
            [
                new_raw_part(
                    menu.encode(),
                    media_type="text/markdown",
                    filename="menu.md",
                )
            ],
            artifact_id="menu-file",
            name="식단표 파일",
        )
        await up.add_artifact(
            [new_data_part(plan)],
            artifact_id="meal-quote",
            name="식사 견적",
        )
        print(f"[식사] 견적: {plan['total']:,}원", flush=True)
        await up.complete()
        # endregion

    async def cancel(self, ctx: RequestContext, queue: EventQueue):
        task = ctx.current_task
        await TaskUpdater(queue, task.id, task.context_id).cancel()


if __name__ == "__main__":
    args = parse_args(
        "보물상사 식사 에이전트",
        step_ms=("끼니 사이 쉬는 시간(ms)", 100),
    )
    serve(card(args.url), CateringExecutor(args.step_ms), args.port)
