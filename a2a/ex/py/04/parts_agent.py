# 받은 파트를 하나씩 말해 주는 에이전트 — 대답은 Task 가 아니라
# Message 하나다. 4부에서 파트의 모양과 수의 타입을 보는 실험용.
from a2a.helpers.proto_helpers import new_message, new_text_part
from a2a.server.agent_execution import AgentExecutor
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from google.protobuf.json_format import MessageToDict

from agents.common import jsonrpc_interface, parse_args, serve


def card(url):
    return AgentCard(
        name="보물상사 파트 확인 에이전트",
        description="받은 파트를 하나씩 말해 줍니다.",
        version="1.0.0",
        supported_interfaces=[jsonrpc_interface(url)],
        capabilities=AgentCapabilities(),
        default_input_modes=["text/plain", "application/json"],
        default_output_modes=["text/plain"],
        skills=[
            AgentSkill(
                id="echo-parts",
                name="파트 확인",
                description="받은 파트의 종류와 값을 돌려줍니다.",
                tags=["debug"],
            )
        ],
    )


# region: describe
def value(v):
    """값 하나: 이 언어가 읽은 타입 이름과 값."""
    return f"{type(v).__name__} {v!r}"


def describe(i, part):
    kind = part.WhichOneof("content")  # text·raw·url·data·None
    if kind == "text":
        line = f"{i}. text {part.text!r}"
    elif kind == "raw":
        line = f"{i}. raw {len(part.raw)}바이트"
    elif kind == "url":
        line = f"{i}. url {part.url}"
    elif kind == "data":
        data = MessageToDict(part.data)  # Value → 파이썬 값
        if isinstance(data, dict):
            kv = [f"{k}: {value(data[k])}" for k in sorted(data)]
            line = f"{i}. data {{{', '.join(kv)}}}"
        else:
            line = f"{i}. data {value(data)}"
    else:  # oneof 가 비었다 — 내용 필드가 하나도 없는 파트
        line = f"{i}. (내용 없음)"
    if part.filename:
        line += f" filename={part.filename}"
    if part.media_type:
        line += f" mediaType={part.media_type}"
    return line


# endregion


# region: execute
class EchoParts(AgentExecutor):
    async def execute(self, ctx, queue):
        lines = [
            describe(i, p) for i, p in enumerate(ctx.message.parts, 1)
        ]
        print("[파트]", " / ".join(lines), flush=True)
        # Task 를 만들지 않고 Message 하나로 답한다(한 줄에 파트 하나)
        reply = new_message(
            [new_text_part(t) for t in lines], context_id=ctx.context_id
        )
        await queue.enqueue_event(reply)

    async def cancel(self, ctx, queue):
        pass


# endregion

args = parse_args("보물상사 파트 확인 에이전트")
serve(card(args.url), EchoParts(), args.port)
# @ norun
