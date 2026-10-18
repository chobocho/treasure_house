# referenceTaskIds 를 SDK 가 작업으로 풀어 주나 — 처리기를 HTTP 없이
# 직접 부른다. 다른 서버의 작업 하나와 이 서버의 작업 하나를 가리킨다.
#   python 15/refs.py
import asyncio

from a2a.helpers import (
    get_message_text,
    new_task_from_user_message,
    new_text_part,
)
from a2a.server.agent_execution import (
    AgentExecutor,
    SimpleRequestContextBuilder,
)
from a2a.server.context import ServerCallContext
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore, TaskUpdater
from a2a.types import Message, Role, SendMessageRequest

from agents.settlement import card


# region: seen
class Seen(AgentExecutor):
    """실행기가 받은 related_tasks 의 id 를 끝 상태 메시지로 알린다."""

    async def execute(self, ctx, queue):
        task = new_task_from_user_message(ctx.message)
        await queue.enqueue_event(task)
        up = TaskUpdater(queue, task.id, task.context_id)
        ids = ", ".join(t.id for t in ctx.related_tasks) or "없음"
        text = f"related_tasks {len(ctx.related_tasks)}개: {ids}"
        await up.complete(up.new_agent_message([new_text_part(text)]))

    async def cancel(self, ctx, queue):
        pass


def handler(fill):
    store = InMemoryTaskStore()
    build = SimpleRequestContextBuilder(
        should_populate_referred_tasks=fill, task_store=store
    )
    return DefaultRequestHandler(
        agent_executor=Seen(),
        task_store=store,
        agent_card=card("http://127.0.0.1:11620/"),
        request_context_builder=build,
    )


# endregion


async def send(h, text, refs=()):
    m = Message(role=Role.ROLE_USER, parts=[new_text_part(text)])
    m.message_id = text
    m.reference_task_ids.extend(refs)
    req = SendMessageRequest(message=m)
    return await h.on_message_send(req, ServerCallContext())


# region: main
async def main():
    other = await send(handler(False), "숙소 견적")  # 다른 서버
    print(f"다른 서버의 작업 {other.id}")
    for fill in (False, True):
        h = handler(fill)
        mine = await send(h, f"앞 작업 {fill}")
        print(f"이 서버의 작업 {mine.id}")
        t = await send(h, f"정산 {fill}", [other.id, mine.id])
        word = "켬" if fill else "끔(기본)"
        print(f"  채우기 {word} → {get_message_text(t.status.message)}")


asyncio.run(main())
# endregion
