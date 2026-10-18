# 기획 에이전트 시험 — HTTP 서버 없이 요청 처리기를 직접 부른다.
#   python 15/test_planner.py
# 명단(--agents)의 주소 11569 에는 아무도 없다 — 발견이 닿지 못한다.
import asyncio
import contextlib
import io
import logging
import re
import sys
import unittest

from a2a.helpers import get_data_parts, get_message_text
from a2a.helpers.proto_helpers import new_text_part
from a2a.server.context import ServerCallContext
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import Message, Role, SendMessageRequest, TaskState

from agents.planner import PlannerExecutor, card

DEAD = "http://127.0.0.1:11569/"
STORY = (
    "2026-10-30부터 1박 2일, 30명(채식 2명), "
    "예산 6,000,000원, 출발 강남역"
)
logging.getLogger("a2a").setLevel(logging.CRITICAL)


# region: tests
class PlannerTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        asyncio.get_running_loop().set_debug(False)
        self.enterContext(contextlib.redirect_stdout(io.StringIO()))
        executor = PlannerExecutor([DEAD], "planner", "planner-secret")
        self.handler = DefaultRequestHandler(
            agent_executor=executor,
            task_store=InMemoryTaskStore(),
            agent_card=card("http://127.0.0.1:11568/"),
        )

    async def say(self, text):
        msg = Message(
            message_id="m-1",
            role=Role.ROLE_USER,
            parts=[new_text_part(text)],
        )
        req = SendMessageRequest(message=msg)
        return await self.handler.on_message_send(
            req, ServerCallContext()
        )

    def asked(self, task):
        self.assertEqual(
            task.status.state, TaskState.TASK_STATE_INPUT_REQUIRED
        )
        return get_data_parts(task.status.message.parts)[0]["missing"]

    async def test_message_counted_once(self):
        task = await self.say(
            "2026-10-30 1박, 채식 2명, 예산 6,000,000원"
        )
        self.assertEqual(self.asked(task), ["headcount"])

    async def test_fullwidth_digits_are_not_a_headcount(self):
        task = await self.say("2026-10-30 1박 ３０명, 예산 6,000,000원")
        self.assertEqual(self.asked(task), ["headcount"])

    async def test_missing_roles_fail_up_front(self):
        task = await self.say(STORY)
        self.assertEqual(task.status.state, TaskState.TASK_STATE_FAILED)
        why = get_message_text(task.status.message)
        self.assertEqual(
            why, "동료를 찾지 못했습니다: 숙소, 식사, 교통, 정산"
        )
        self.assertNotIn("127.0.0.1", why)  # 안쪽 명단은 새지 않는다


# endregion


class NoClock(io.TextIOBase):
    """'Ran 3 tests in 0.512s' 의 시간만 가린다(실행마다 달라서)."""

    def write(self, s):
        return sys.stdout.write(re.sub(r"in \d+\.\d+s$", "in <초>", s))


if __name__ == "__main__":
    runner = unittest.TextTestRunner(stream=NoClock(), verbosity=2)
    unittest.main(testRunner=runner)
# @ norun
