# 규칙을 어기는 실행기 일곱 — 처리기는 무엇을 잡고, 무엇을 저장하나.
#   python 07/rules.py
import asyncio
import logging

from a2a.helpers import new_task_from_user_message, new_text_message
from a2a.server.agent_execution import AgentExecutor
from a2a.server.context import ServerCallContext
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore, TaskUpdater
from a2a.types import (
    InvalidParamsError,
    ListTasksRequest,
    Message,
    Part,
    Role,
    SendMessageRequest,
    Task,
    TaskState,
)
from a2a.utils.errors import A2AError
from step1_echo import card


class Bad(AgentExecutor):
    async def cancel(self, ctx, q):  # 이 실험에서는 안 쓴다
        pass


# region: bad
class TwoMessages(Bad):  # Message 는 하나만
    async def execute(self, ctx, q):
        await q.enqueue_event(new_text_message("하나"))
        await q.enqueue_event(new_text_message("둘"))


class StatusFirst(Bad):  # Task 보다 상태가 먼저
    async def execute(self, ctx, q):
        await TaskUpdater(q, ctx.task_id, ctx.context_id).start_work()


class MessageAfterTask(Bad):  # Task 다음에 Message
    async def execute(self, ctx, q):
        await q.enqueue_event(new_task_from_user_message(ctx.message))
        await q.enqueue_event(new_text_message("끝났습니다"))


class OtherId(Bad):  # ctx.task_id 와 다른 id
    async def execute(self, ctx, q):
        task = new_task_from_user_message(ctx.message)
        task.id = "my-own-id"
        await q.enqueue_event(task)


class Silent(Bad):  # 아무것도 싣지 않고 돌아간다
    async def execute(self, ctx, q):
        return


class Refuses(Bad):  # A2A 오류를 던진다
    async def execute(self, ctx, q):
        raise InvalidParamsError(message="인원이 없습니다")


class Crashes(Bad):  # 아무 예외나 던진다
    async def execute(self, ctx, q):
        raise RuntimeError("견적표를 못 읽었습니다")


# endregion


# region: try
async def attempt(executor):
    store = InMemoryTaskStore()
    handler = DefaultRequestHandler(
        agent_executor=executor(), task_store=store, agent_card=CARD
    )
    msg = Message(message_id="m-1", role=Role.ROLE_USER)
    msg.parts.append(Part(text="30명"))
    send = handler.on_message_send(
        SendMessageRequest(message=msg), CALL
    )
    try:
        got = await asyncio.wait_for(send, timeout=2)
        what = type(got).__name__
        if isinstance(got, Task):
            what += " " + TaskState.Name(got.status.state)
    except (A2AError, RuntimeError, TimeoutError) as e:
        what = f"{type(e).__name__}: {str(e) or '2초 동안 답이 없다'}"
    page = await store.list(ListTasksRequest(), CALL)
    saved = [TaskState.Name(t.status.state) for t in page.tasks]
    print(f"{executor.__name__}\n  답 {what}\n  저장 {saved}")


# endregion

CARD, CALL = card("http://127.0.0.1:10700/"), ServerCallContext()
logging.disable(logging.ERROR)  # SDK 의 오류 기록(추적 정보)은 끈다
for cls in (
    TwoMessages,
    StatusFirst,
    MessageAfterTask,
    OtherId,
    Silent,
    Refuses,
    Crashes,
):
    asyncio.run(attempt(cls))
