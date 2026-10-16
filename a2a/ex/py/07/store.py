# InMemoryTaskStore 의 두 성질 — 소유자별 분리, 그리고 사본.
#   python 07/store.py
import asyncio

from a2a.auth.user import User
from a2a.server.context import ServerCallContext
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import Task, TaskState


class Staff(User):
    """로그인한 직원 — 인증은 12부, 여기서는 이름만 단다."""

    def __init__(self, name):
        self.name = name

    is_authenticated = property(lambda self: True)
    user_name = property(lambda self: self.name)


kim = ServerCallContext(user=Staff("kim"))
lee = ServerCallContext(user=Staff("lee"))
anon = ServerCallContext()  # 익명 — user_name 은 ""


# region: owner
async def owners():
    store = InMemoryTaskStore()
    await store.save(Task(id="t-1", context_id="c-1"), kim)
    for who, call in (("kim ", kim), ("lee ", lee), ("익명", anon)):
        found = await store.get("t-1", call)
        print(f"{who} 이 t-1 을 찾으면:", found is not None)


# endregion


# region: copy
async def copies(use_copying):
    store = InMemoryTaskStore(use_copying=use_copying)
    await store.save(Task(id="t-2", context_id="c-2"), anon)
    got = await store.get("t-2", anon)
    got.status.state = TaskState.TASK_STATE_COMPLETED  # save 없이 고침
    again = await store.get("t-2", anon)
    state = TaskState.Name(again.status.state)
    print(f"use_copying={use_copying}: 다시 꺼낸 상태 {state}")


# endregion


async def main():
    await owners()
    await copies(True)
    await copies(False)


asyncio.run(main())
