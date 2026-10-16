# 기능(capabilities)을 하나도 켜지 않은 에이전트 — 인사만 한다.
# 카드에 없는 기능을 부르면 서버가 무엇을 돌려주는지 보는 실험용.
from a2a.helpers.proto_helpers import new_text_message
from a2a.server.agent_execution import AgentExecutor
from a2a.types import AgentCapabilities, AgentCard, AgentSkill

from agents.common import jsonrpc_interface, parse_args, serve


# region: card
def card(url):
    return AgentCard(
        name="보물상사 안내 에이전트",
        description="인사만 합니다. 켜 둔 기능이 없습니다.",
        version="1.0.0",
        supported_interfaces=[jsonrpc_interface(url)],
        capabilities=AgentCapabilities(),  # 아무것도 켜지 않는다
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain"],
        skills=[
            AgentSkill(
                id="greet",
                name="인사",
                description="인사를 돌려줍니다.",
                tags=["greeting"],
            )
        ],
    )


# endregion


class Greeter(AgentExecutor):
    async def execute(self, ctx, queue):
        reply = "안녕하세요, 보물상사입니다."
        await queue.enqueue_event(
            new_text_message(reply, context_id=ctx.context_id)
        )

    async def cancel(self, ctx, queue):
        pass


args = parse_args("보물상사 안내 에이전트")
serve(card(args.url), Greeter(), args.port)
# @ norun
