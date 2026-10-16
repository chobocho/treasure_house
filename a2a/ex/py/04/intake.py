# 접수 에이전트 — 카드의 입력 모드 밖의 미디어 타입은 거절하고(5장),
# 인원("30명")이 없으면 되묻는다(6장의 작업 만들기용).
# 파이썬 SDK 는 요청 처리기의 스위치 하나로 미디어 타입을 검사한다.
import re

from a2a.helpers.proto_helpers import new_text_part
from a2a.server.agent_execution import AgentExecutor
from a2a.types import AgentCapabilities, AgentCard, AgentSkill

from agents.common import begin, jsonrpc_interface, parse_args, serve


def card(url):
    return AgentCard(
        name="보물상사 접수 에이전트",
        description="글과 JSON 만 받습니다.",
        version="1.0.0",
        supported_interfaces=[jsonrpc_interface(url)],
        capabilities=AgentCapabilities(),
        default_input_modes=["text/plain", "application/json"],
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
    async def execute(self, ctx, queue):
        _, up = await begin(ctx, queue)
        text = " ".join(p.text for p in ctx.message.parts)
        if m := re.search(r"(\d+)명", text):
            print(f"[접수] {m[1]}명", flush=True)
            receipt = new_text_part(f"{m[1]}명 접수했습니다")
            await up.add_artifact([receipt], name="접수증")
            await up.complete()
        else:
            print("[접수] 되묻기", flush=True)
            ask = new_text_part("인원은 몇 명입니까?")
            await up.requires_input(up.new_agent_message([ask]))

    async def cancel(self, ctx, queue):
        pass


args = parse_args("보물상사 접수 에이전트")
# region: strict
serve(card(args.url), Intake(), args.port, validate_input_modes=True)
# endregion
# @ norun
