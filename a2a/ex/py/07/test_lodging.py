# 숙소 에이전트 시험 — HTTP 없이 요청 처리기를 직접 부른다.
#   python 07/test_lodging.py
# 업무 규칙의 골든 시험(workshop/test_domain.py)과 같은 unittest 다.
import asyncio
import contextlib
import io
import json
import logging
import re
import sys
import unittest
from pathlib import Path

from a2a.helpers import (
    get_data_parts,
    get_message_text,
    new_data_part,
    new_text_part,
)
from a2a.server.context import ServerCallContext
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import Message, Role, SendMessageRequest, TaskState

from agents.lodging import LodgingExecutor, card

GOLDEN = Path(__file__).resolve().parents[2] / "fixtures/golden"
CASES = json.loads((GOLDEN / "domain.json").read_text())
DONE = TaskState.TASK_STATE_COMPLETED
ASKING = TaskState.TASK_STATE_INPUT_REQUIRED
# SDK 가 때때로 남기는 경고("Dispatcher task is not running…")는
# 타이밍에 따라 나왔다 말았다 해서 시험 출력에서 뺀다.
logging.getLogger("a2a").setLevel(logging.ERROR)


# region: fixture
class LodgingTest(unittest.IsolatedAsyncioTestCase):
    executor = LodgingExecutor  # 하위 클래스가 바꿔 끼운다

    async def asyncSetUp(self):
        # 이 시험 틀은 asyncio 디버그 모드로 돈다. 느린 콜백 경고가
        # 실행마다 달라 끈다(이 기계는 느리다).
        asyncio.get_running_loop().set_debug(False)
        # 에이전트의 서버 로그는 시험의 관심사가 아니다
        self.enterContext(contextlib.redirect_stdout(io.StringIO()))
        self.handler = DefaultRequestHandler(
            agent_executor=self.executor(),
            task_store=InMemoryTaskStore(),
            agent_card=card("http://127.0.0.1:10700/"),
        )
        self.call = ServerCallContext()
        self.n = 0

    async def say(self, *parts, task=None):
        """사용자 메시지 하나를 보내고 막는 호출의 Task 를 받는다."""
        self.n += 1
        msg = Message(
            message_id=f"m-{self.n}", role=Role.ROLE_USER, parts=parts
        )
        if task is not None:  # 이어 말하기
            msg.task_id, msg.context_id = task.id, task.context_id
        req = SendMessageRequest(message=msg)
        return await self.handler.on_message_send(req, self.call)


# endregion


# region: tests
class Tests(LodgingTest):
    async def test_golden(self):
        for case in CASES["chooseLodging"]:
            with self.subTest(case=case["name"]):
                task = await self.say(new_data_part(case["input"]))
                if case["expected"]["ok"]:
                    self.assertEqual(task.status.state, DONE)
                    data = get_data_parts(task.artifacts[0].parts)[0]
                    self.assertEqual(data, case["expected"])
                else:
                    text = get_message_text(task.status.message)
                    self.assertEqual(text, case["expected"]["reason"])

    async def test_asks_for_first_missing(self):
        task = await self.say(new_text_part("숙소 부탁합니다"))
        self.assertEqual(task.status.state, ASKING)
        data = get_data_parts(task.status.message.parts)[0]
        self.assertEqual(
            data["missing"], ["date", "nights", "headcount"]
        )

    async def test_follow_up_completes(self):
        req = {"date": "2026-10-30", "nights": 1}
        task = await self.say(new_data_part(req))
        task = await self.say(new_text_part("30명"), task=task)
        self.assertEqual(task.status.state, DONE)
        data = get_data_parts(task.artifacts[0].parts)[0]
        self.assertEqual(data["total"], 2_100_000)

    async def test_hears_only_the_user(self):
        task = await self.say(new_text_part("숙소 부탁합니다"))
        for line in ["30명", "1박", "2026-11-06"]:
            if task.status.state != ASKING:
                break  # 끝난 작업에는 더 말할 수 없다
            task = await self.say(new_text_part(line), task=task)
        self.assertEqual(task.status.state, DONE)
        data = get_data_parts(task.artifacts[0].parts)[0]
        self.assertEqual(data["venueId"], "chuncheon-lake")


# endregion


class NoClock(io.TextIOBase):
    """'Ran 4 tests in 0.512s' 의 시간만 가린다(실행마다 달라서)."""

    def write(self, s):
        return sys.stdout.write(re.sub(r"in \d+\.\d+s$", "in <초>", s))


def main(module="__main__"):
    runner = unittest.TextTestRunner(stream=NoClock(), verbosity=2)
    unittest.main(module=module, testRunner=runner)


if __name__ == "__main__":
    main()
# @ timeout: 60
