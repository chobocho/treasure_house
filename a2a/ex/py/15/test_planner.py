# 기획 에이전트 시험 — HTTP 서버 없이 요청 처리기를 직접 부른다.
#   python 15/test_planner.py
# 명단(--agents)의 주소 11569 에는 아무도 없다 — 발견이 닿지 못한다.
import asyncio
import contextlib
import io
import json
import logging
import re
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from a2a.helpers import get_data_parts, get_message_text
from a2a.helpers.proto_helpers import new_text_part
from a2a.server.context import ServerCallContext
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    Message,
    Role,
    SendMessageRequest,
    Task,
    TaskState,
    TaskStatus,
)

from agents.planner import PlannerExecutor, card
from agents.settlement import card as settle_card

DEAD = "http://127.0.0.1:11569/"
STORY = (
    "2026-10-30부터 1박 2일, 30명(채식 2명), "
    "예산 6,000,000원, 출발 강남역"
)
logging.getLogger("a2a").setLevel(logging.CRITICAL)
AUTH = TaskState.TASK_STATE_AUTH_REQUIRED
CALLS = []  # 가짜 정산이 받은 (메서드, 작업 id)


class FakeSettlement(BaseHTTPRequestHandler):
    """가짜 정산 — 토큰을 주고, 받은 JSON-RPC 메서드를 적어 둔다."""

    def do_POST(self):
        body = self.rfile.read(int(self.headers["Content-Length"]))
        if self.path == "/oauth/token":
            out = {"access_token": "tok-fake", "token_type": "Bearer"}
        else:
            rpc = json.loads(body)
            CALLS.append((rpc["method"], rpc["params"]["id"]))
            task = {"id": rpc["params"]["id"], "contextId": "c-1"}
            task["status"] = {"state": "TASK_STATE_CANCELED"}
            out = {"jsonrpc": "2.0", "id": rpc["id"], "result": task}
        raw = json.dumps(out).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def log_message(self, *args):
        pass


# region: tests
class PlannerTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        asyncio.get_running_loop().set_debug(False)
        self.enterContext(contextlib.redirect_stdout(io.StringIO()))
        self.executor = PlannerExecutor(
            [DEAD], "planner", "planner-secret"
        )
        self.store = InMemoryTaskStore()
        self.handler = DefaultRequestHandler(
            agent_executor=self.executor,
            task_store=self.store,
            agent_card=card("http://127.0.0.1:11568/"),
        )

    async def say(self, text, task_id=""):
        msg = Message(
            message_id="m-1",
            role=Role.ROLE_USER,
            parts=[new_text_part(text)],
            task_id=task_id,
            context_id="c-1" if task_id else "",
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

    async def test_denial_cancels_settlement(self):
        # 결재를 기다리는 기획 작업 하나를 저장소와 waiting 에 놓는다
        fake = ThreadingHTTPServer(("127.0.0.1", 0), FakeSettlement)
        threading.Thread(target=fake.serve_forever, daemon=True).start()
        url = f"http://127.0.0.1:{fake.server_port}/"
        mine = Task(id="plan-1", context_id="c-1")
        mine.status.CopyFrom(TaskStatus(state=AUTH))
        await self.store.save(mine, ServerCallContext())
        settle = Task(id="settle-1", context_id="c-1")
        cards = {"settle": settle_card(url)}
        self.executor.waiting["plan-1"] = (cards, {}, [], settle)
        task = await self.say("안 됩니다", task_id="plan-1")
        fake.shutdown()
        self.assertEqual(
            task.status.state, TaskState.TASK_STATE_REJECTED
        )
        # 반려하면 정산 쪽에서 기다리던 작업도 거둔다
        self.assertEqual(CALLS, [("CancelTask", "settle-1")])
        self.assertEqual(self.executor.waiting, {})


# endregion


class NoClock(io.TextIOBase):
    """'Ran 3 tests in 0.512s' 의 시간만 가린다(실행마다 달라서)."""

    def write(self, s):
        return sys.stdout.write(re.sub(r"in \d+\.\d+s$", "in <초>", s))


if __name__ == "__main__":
    runner = unittest.TextTestRunner(stream=NoClock(), verbosity=2)
    unittest.main(testRunner=runner)
# @ norun
