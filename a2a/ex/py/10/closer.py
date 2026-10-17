# 종료 실험 에이전트 — 첫 글 파트로 고른 차례대로 상태를 싣고
# 돌아간다. SDK 가 스트림을 언제 닫는지 보려는 실험용이다(3장).
# 서버는 SDK 기본값 그대로다.
import asyncio

from a2a.helpers.proto_helpers import (
    get_message_text,
    new_text_message,
)
from a2a.server.agent_execution import AgentExecutor
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
    TaskState,
)

from agents.common import begin, jsonrpc_interface, parse_args, serve

# region: plans
# 고른 말 → 실행기가 싣는 상태들. "쉼" 은 0.3초 쉬기,
# "BOOM" 은 예외 던지기. MESSAGE 는 Task 없이 Message 하나.
PLANS = {
    "COMPLETED": ["WORKING", "COMPLETED"],
    "INPUT_REQUIRED": ["INPUT_REQUIRED"],
    "AUTH_REQUIRED": ["AUTH_REQUIRED"],
    "WORKING": ["WORKING"],  # 끝 상태 없이 돌아간다
    "LATE": ["INPUT_REQUIRED", "쉼", "WORKING", "COMPLETED"],
    "BOOM": ["WORKING", "쉼", "BOOM"],
    "MESSAGE": [],
}
# endregion


def card(url):
    return AgentCard(
        name="보물상사 종료 실험 에이전트",
        description="고른 상태에서 실행을 끝냅니다.",
        version="1.0.0",
        supported_interfaces=[jsonrpc_interface(url)],
        capabilities=AgentCapabilities(streaming=True),
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain"],
        skills=[
            AgentSkill(
                id="close",
                name="종료 실험",
                description="스트림 종료 실험",
                tags=["debug"],
            )
        ],
    )


# region: execute
class Closer(AgentExecutor):
    async def execute(self, ctx, queue):
        word = get_message_text(ctx.message)
        if word == "MESSAGE":
            await queue.enqueue_event(new_text_message("메시지로 답함"))
            return
        _, up = await begin(ctx, queue)  # Task(SUBMITTED) 가 먼저
        for step in PLANS[word]:
            if step == "쉼":
                await asyncio.sleep(0.3)
            elif step == "BOOM":
                print(f"[종료] {word}: 예외를 던진다", flush=True)
                raise RuntimeError("실행기가 넘어졌다")
            else:
                await up.update_status(
                    TaskState.Value("TASK_STATE_" + step)
                )
        print(f"[종료] {word}: 실행기가 돌아갔다", flush=True)

    # endregion

    async def cancel(self, ctx, queue):
        pass  # 실험에서는 취소하지 않는다


args = parse_args("보물상사 종료 실험 에이전트")
serve(card(args.url), Closer(), args.port)
# @ norun
