# 고장 에이전트 — 일하다 실패한다. 실패를 알리는 세 가지 길(6장):
#   직접 — 실행기가 FAILED 를 싣고 까닭을 status.message 에 적는다
#   나중 — Task·WORKING 을 실은 뒤 예외를 던진다
#   먼저 — 아무 이벤트도 싣기 전에 예외를 던진다
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
)

from agents.common import jsonrpc_interface, parse_args, serve


def card(url):
    return AgentCard(
        name="보물상사 고장 에이전트",
        description="일하다 실패합니다.",
        version="1.0.0",
        supported_interfaces=[jsonrpc_interface(url)],
        capabilities=AgentCapabilities(),
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain"],
        skills=[
            AgentSkill(
                id="broken",
                name="고장",
                description="실패 실험",
                tags=["debug"],
            )
        ],
    )


# region: execute
class Broken(AgentExecutor):
    async def execute(self, ctx, queue):
        how = get_message_text(ctx.message)
        print(f"[고장] {how}", flush=True)
        if how == "먼저":  # 이벤트를 하나도 싣기 전에
            raise RuntimeError("장부 파일을 열 수 없습니다")
        task = new_task_from_user_message(ctx.message)
        await queue.enqueue_event(task)
        up = TaskUpdater(queue, task.id, task.context_id)
        await up.start_work()
        if how == "나중":  # Task 를 실은 뒤에
            raise RuntimeError("장부 파일을 열 수 없습니다")
        # 직접: 실패도 상태 갱신이다 — 까닭을 메시지로
        why = [new_text_part("장부 파일을 열 수 없습니다")]
        await up.failed(up.new_agent_message(why))

    # endregion

    async def cancel(self, ctx, queue):
        pass


args = parse_args("보물상사 고장 에이전트")
serve(card(args.url), Broken(), args.port)
# @ norun
