# HTTP 층까지 시험하되 포트는 열지 않는다 — Starlette 앱을 프로세스
# 안에서 부른다. SDK 클라이언트까지 붙인 시험도 하나 있다.
#   python 07/test_http.py
import contextlib
import io
import unittest

import httpx
import test_lodging
from a2a.client import ClientConfig, create_client
from a2a.helpers import new_text_message
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import (
    create_agent_card_routes,
    create_jsonrpc_routes,
)
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import Role, SendMessageRequest, TaskState
from starlette.applications import Starlette
from starlette.testclient import TestClient

from agents.lodging import LodgingExecutor, card

URL = "http://lodging.test/"  # 이름만 있는 주소 — 연결은 없다


# region: app
def make_app():
    """common.serve 가 uvicorn 에 넘기는 것과 같은 앱."""
    c = card(URL)
    handler = DefaultRequestHandler(
        agent_executor=LodgingExecutor(),
        task_store=InMemoryTaskStore(),
        agent_card=c,
    )
    routes = create_agent_card_routes(c)
    routes += create_jsonrpc_routes(handler, "/")
    return c, Starlette(routes=routes)


# endregion


# region: wire
class WireTest(unittest.TestCase):
    def setUp(self):
        self.enterContext(contextlib.redirect_stdout(io.StringIO()))

    def test_send_message_on_the_wire(self):
        _, app = make_app()
        web = TestClient(app, base_url=URL)
        card_json = web.get("/.well-known/agent-card.json").json()
        self.assertEqual(card_json["name"], "보물상사 숙소 에이전트")
        data = {"date": "2026-10-30", "nights": 1, "headcount": 30}
        body = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "SendMessage",
            "params": {
                "message": {
                    "messageId": "w-1",
                    "role": "ROLE_USER",
                    "parts": [{"data": data}],
                }
            },
        }
        r = web.post("/", json=body, headers={"A2A-Version": "1.0"})
        task = r.json()["result"]["task"]
        self.assertEqual(
            task["status"]["state"], "TASK_STATE_COMPLETED"
        )
        quote = task["artifacts"][0]["parts"][0]["data"]
        self.assertEqual(quote["total"], 2100000)  # 와이어엔 2100000.0
        bad = web.post("/", json={**body, "method": "Nope"})
        self.assertEqual(bad.json()["error"]["code"], -32601)


# endregion


# region: client
class ClientTest(test_lodging.LodgingTest):
    async def test_sdk_client_without_network(self):
        c, app = make_app()
        http = httpx.AsyncClient(transport=httpx.ASGITransport(app=app))
        client = await create_client(c, ClientConfig(httpx_client=http))
        msg = new_text_message("숙소 부탁합니다", role=Role.ROLE_USER)
        states = []
        async for ev in client.send_message(
            SendMessageRequest(message=msg)
        ):
            kind = ev.WhichOneof("payload")
            state = getattr(ev, kind).status.state
            states.append(TaskState.Name(state)[11:])
        await client.close()
        self.assertEqual(states, ["SUBMITTED", "INPUT_REQUIRED"])


# endregion

if __name__ == "__main__":
    test_lodging.main()
# @ timeout: 60
