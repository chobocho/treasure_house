# 고집 에이전트 — 상태를 앞뒤로 옮겨 보고, 끝난 뒤에도 옮겨 본다.
# SDK 가 어느 전이를 막는지 보려는 실험용이다(2장).
import asyncio

from a2a.helpers.proto_helpers import new_task_from_user_message
from a2a.server.agent_execution import AgentExecutor
from a2a.server.tasks import TaskUpdater
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
    TaskState,
)

from agents.common import jsonrpc_interface, parse_args, serve


def card(url):
    return AgentCard(
        name="보물상사 고집 에이전트",
        description="상태를 마음대로 옮겨 봅니다.",
        version="1.0.0",
        supported_interfaces=[jsonrpc_interface(url)],
        capabilities=AgentCapabilities(),
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain"],
        skills=[
            AgentSkill(
                id="stubborn",
                name="고집",
                description="상태 전이 실험",
                tags=["debug"],
            )
        ],
    )


# region: execute
async def put(up, name, who=""):
    try:
        await up.update_status(TaskState.Value("TASK_STATE_" + name))
        print(f"[고집] {who}{name} 실음", flush=True)
    except RuntimeError as e:
        print(f"[고집] {who}{name} 거절: {e}", flush=True)


class Stubborn(AgentExecutor):
    async def execute(self, ctx, queue):
        task = new_task_from_user_message(ctx.message)  # SUBMITTED
        await queue.enqueue_event(task)
        up = TaskUpdater(queue, task.id, task.context_id)
        # 앞으로, 뒤로(접수로 되돌리기), 끝
        for name in ("WORKING", "SUBMITTED", "COMPLETED"):
            await put(up, name)
        await asyncio.sleep(0.2)  # 끝낸 뒤 조금 있다가 또 옮긴다
        await put(up, "WORKING")
        # 갱신기를 새로 만들면 그 검사를 비켜 간다
        fresh = TaskUpdater(queue, task.id, task.context_id)
        await put(fresh, "WORKING", "새 갱신기로 ")

    # endregion

    async def cancel(self, ctx, queue):
        pass


args = parse_args("보물상사 고집 에이전트")
serve(card(args.url), Stubborn(), args.port)
# @ norun
