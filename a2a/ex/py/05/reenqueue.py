# 접수 에이전트(파이썬) — 이어 말하기에서 Task 를 다시 싣는 판과
# 싣지 않는 판을 견준다(5장). --always 1 이면 늘 Task 부터 싣는다.
import re

from a2a.helpers.proto_helpers import (
    get_message_text,
    new_task_from_user_message,
    new_text_part,
)
from a2a.server.agent_execution import AgentExecutor
from a2a.server.tasks import TaskUpdater
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
    Task,
    TaskState,
)

from agents.common import jsonrpc_interface, parse_args, serve


def card(url):
    return AgentCard(
        name="보물상사 접수 에이전트",
        description="인원을 받아 접수증을 냅니다.",
        version="1.0.0",
        supported_interfaces=[jsonrpc_interface(url)],
        capabilities=AgentCapabilities(streaming=True),
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain"],
        skills=[
            AgentSkill(
                id="intake",
                name="접수",
                description="인원을 받아 접수증을 냅니다.",
                tags=["debug"],
            )
        ],
    )


class Intake(AgentExecutor):
    def __init__(self, always):
        self.always = always

    # region: begin
    async def execute(self, ctx, queue):
        if ctx.current_task is None:  # 첫 마디 — 새 Task 를 싣는다
            task = new_task_from_user_message(ctx.message)
            await queue.enqueue_event(task)
        else:
            task = Task()
            task.CopyFrom(ctx.current_task)
            if self.always:  # 이어 말하기에도 Task 부터(§3.1.2 대로)
                task.status.Clear()
                task.status.state = TaskState.TASK_STATE_WORKING
                await queue.enqueue_event(task)
        up = TaskUpdater(queue, task.id, task.context_id)
        # endregion
        if m := re.search(r"(\d+)명", get_message_text(ctx.message)):
            receipt = new_text_part(f"{m[1]}명 접수했습니다")
            await up.add_artifact([receipt], name="접수증")
            await up.complete()
        else:
            ask = new_text_part("인원은 몇 명입니까?")
            await up.requires_input(up.new_agent_message([ask]))

    async def cancel(self, ctx, queue):
        pass


if __name__ == "__main__":
    args = parse_args("접수 에이전트", always=("Task 를 늘 싣는다", 0))
    serve(card(args.url), Intake(args.always), args.port)
# @ norun
