"""교통 에이전트 — 버스를 고르고, 시간이 걸리는 배차를 진행한다.

보여 주는 것: returnImmediately 로 바로 돌려받는 Task, 오래 걸리는
작업의 단계별 상태 갱신, 푸시 알림(웹훅), GetTask 폴링, ListTasks,
CancelTask(→ CANCELED), SubscribeToTask.
"""

import asyncio

import httpx
from a2a.helpers.proto_helpers import (
    new_data_part,
    new_task_from_user_message,
    new_text_part,
)
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import (
    BasePushNotificationSender,
    InMemoryPushNotificationConfigStore,
    TaskUpdater,
)
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
    TaskState,
)

from agents.common import (
    PROVIDER,
    as_ints,
    data_of,
    jsonrpc_interface,
    parse_args,
    serve,
)
from workshop import domain
from workshop.fixtures import workshop


def card(url):
    return AgentCard(
        name="보물상사 교통 에이전트",
        description="인원과 박 수로 버스를 고르고 배차합니다.",
        version="1.0.0",
        provider=PROVIDER,
        supported_interfaces=[jsonrpc_interface(url)],
        capabilities=AgentCapabilities(
            streaming=True, push_notifications=True
        ),
        default_input_modes=["application/json"],
        default_output_modes=["application/json"],
        skills=[
            AgentSkill(
                id="book-bus",
                name="버스 배차",
                description="전세 버스를 고르고 배차까지 진행합니다.",
                tags=["transport", "workshop"],
                examples=[
                    '{"headcount":30,"nights":1,"depart":"강남역"}'
                ],
            )
        ],
    )


def vehicles_text(plan):
    """[{"id":"bus45","count":1}] → 45인승 1대"""
    seats = {b["id"]: b["seats"] for b in workshop()["buses"]}
    return ", ".join(
        f"{seats[v['id']]}인승 {v['count']}대" for v in plan["vehicles"]
    )


class BusExecutor(AgentExecutor):
    def __init__(self, step_ms):
        self.step = step_ms / 1000  # 배차 단계 하나에 걸리는 시간

    async def execute(self, ctx: RequestContext, queue: EventQueue):
        task = ctx.current_task or new_task_from_user_message(
            ctx.message
        )
        if ctx.current_task is None:
            await queue.enqueue_event(task)
        up = TaskUpdater(queue, task.id, task.context_id)
        req = as_ints(data_of(ctx.message), "headcount", "nights")
        plan = domain.choose_buses(req)
        if not plan["ok"]:
            print(f"[교통] 거절: {plan['reason']}", flush=True)
            await up.reject(
                up.new_agent_message([new_text_part(plan["reason"])])
            )
            return
        for step in workshop()["busSteps"]:
            await asyncio.sleep(self.step)  # 취소되면 여기서 끊긴다
            print(f"[교통] {step}", flush=True)
            await up.update_status(
                TaskState.TASK_STATE_WORKING,
                up.new_agent_message([new_text_part(step)]),
            )
        depart = req.get("depart") or "미정"  # 없거나 null 이면
        summary = (
            f"{vehicles_text(plan)}, {plan['days']}일, "
            f"{plan['total']:,}원, 출발 {depart}"
        )
        await up.add_artifact(
            [new_data_part(plan), new_text_part(summary)],
            artifact_id="bus-booking",
            name="배차 확인서",
        )
        print(f"[교통] 완료: {summary}", flush=True)
        await up.complete()

    async def cancel(self, ctx: RequestContext, queue: EventQueue):
        task = ctx.current_task
        print("[교통] 취소", flush=True)
        up = TaskUpdater(queue, task.id, task.context_id)
        await up.cancel(
            up.new_agent_message([new_text_part("배차를 취소했습니다")])
        )


if __name__ == "__main__":
    args = parse_args(
        "보물상사 교통 에이전트",
        step_ms=("배차 단계 하나의 시간(ms)", 300),
    )
    store = InMemoryPushNotificationConfigStore()
    serve(
        card(args.url),
        BusExecutor(args.step_ms),
        args.port,
        push_config_store=store,
        push_sender=BasePushNotificationSender(
            httpx.AsyncClient(), store
        ),
    )
