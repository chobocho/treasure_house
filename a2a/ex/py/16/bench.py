# 오류 시험대 — 완성 에이전트로는 일으킬 수 없는 오류를 일부러 낸다.
# 카드는 확장 카드 기능을 켰지만 확장 카드를 두지 않았다(-32007).
# 실행기는 받은 글에 따라 규칙을 어긴다:
#   "차례 위반" — Task 보다 상태 갱신을 먼저 싣는다(-32006)
#   "고장"      — 예외를 던진다(-32603)
#   그 밖       — 받은 글을 Message 로 돌려준다
#   python 16/bench.py --port P
from a2a.helpers.proto_helpers import get_message_text, new_text_message
from a2a.server.agent_execution import AgentExecutor
from a2a.server.tasks import TaskUpdater
from a2a.types import AgentCapabilities, AgentCard, AgentSkill

from agents.common import jsonrpc_interface, parse_args, serve


# region: card
def card(url):
    return AgentCard(
        name="보물상사 시험대 에이전트",
        description="오류를 일부러 냅니다.",
        version="1.0.0",
        supported_interfaces=[jsonrpc_interface(url)],
        # 확장 카드를 준다고 적고, 처리기에는 넘기지 않는다
        capabilities=AgentCapabilities(
            streaming=True, extended_agent_card=True
        ),
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain"],
        skills=[
            AgentSkill(
                id="misbehave",
                name="규칙 어기기",
                description="받은 글에 따라 규칙을 어깁니다.",
                tags=["test"],
            )
        ],
    )


# endregion


# region: execute
class Bench(AgentExecutor):
    async def execute(self, ctx, queue):
        said = get_message_text(ctx.message)
        if said == "차례 위반":
            up = TaskUpdater(queue, ctx.task_id, ctx.context_id)
            await up.start_work()  # Task 를 싣기 전에 상태부터
        elif said == "고장":
            raise RuntimeError("시험대가 고장 났습니다")
        else:
            await queue.enqueue_event(
                new_text_message(said, context_id=ctx.context_id)
            )

    # endregion

    async def cancel(self, ctx, queue):
        pass


args = parse_args("보물상사 시험대 에이전트")
serve(card(args.url), Bench(), args.port)
# @ norun
