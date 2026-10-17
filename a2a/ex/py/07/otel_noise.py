# 5부에서 본 "Failed to detach context" 는 어디서 오나 — 끝난 작업에
# 이어 말하는 요청을 서버(같은 프로세스 안의 uvicorn)에 보내고, 그동안
# 남은 로그를 로거·첫 줄로 센다. 원격 측정을 켜고(on)·끄고(off).
#   python 07/otel_noise.py on|off PORT
import os
import sys

# region: switch
if sys.argv[1] == "off":  # SDK 가 import 될 때 한 번 읽는다
    os.environ["OTEL_INSTRUMENTATION_A2A_SDK_ENABLED"] = "false"
# endregion

import asyncio
import collections
import gc
import logging
import re

import uvicorn
from a2a.client import ClientConfig, create_client
from a2a.helpers import new_data_part
from a2a.server.request_handlers import (
    DefaultRequestHandler,
)
from a2a.server.routes import (
    create_agent_card_routes,
    create_jsonrpc_routes,
)
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import Message, Role, SendMessageRequest
from a2a.utils import telemetry
from a2a.utils.errors import A2AError
from starlette.applications import Starlette

from agents.lodging import LodgingExecutor, card

SEEN = collections.Counter()


class Count(logging.Handler):
    """로그 한 건을 '로거: 첫 줄 [버려진 코루틴]' 으로 센다."""

    def emit(self, record):
        text = record.getMessage()
        first = re.sub(r" \(ID: [^)]*\)", "", text.splitlines()[0])
        coro = re.search(r"coro=<([\w.]+)\(", text)
        where = f" [{coro.group(1)}]" if coro else ""
        SEEN[f"{record.name}: {first[:40]}{where}"] += 1


def app(url):
    c = card(url)
    handler = DefaultRequestHandler(
        agent_executor=LodgingExecutor(),
        task_store=InMemoryTaskStore(),
        agent_card=c,
    )
    routes = create_agent_card_routes(c) + create_jsonrpc_routes(
        handler, "/"
    )
    return Starlette(routes=routes)


def msg(n, data, task=None):
    m = Message(
        message_id=f"o-{n}",
        role=Role.ROLE_USER,
        parts=[new_data_part(data)],
    )
    if task:
        m.task_id, m.context_id = task.id, task.context_id
    return SendMessageRequest(message=m)


# region: provoke
async def provoke(url):
    full = {"date": "2026-10-30", "nights": 1, "headcount": 30}
    task = None
    for streaming in (False, True):
        client = await create_client(
            url, ClientConfig(streaming=streaming)
        )
        async for ev in client.send_message(msg(1, full)):
            task = ev.task if ev.HasField("task") else task
        try:  # 끝난 작업에 곧바로 한마디 더
            async for _ in client.send_message(msg(2, full, task)):
                pass
        except A2AError as e:
            print("거절:", type(e).__name__)
        await client.close()


# endregion


async def main(port):
    logging.getLogger().addHandler(Count())
    url = f"http://127.0.0.1:{port}/"
    config = uvicorn.Config(app(url), port=port, log_level="error")
    server = uvicorn.Server(config)
    serving = asyncio.create_task(server.serve())
    while not server.started:
        await asyncio.sleep(0.05)
    await provoke(url)
    server.should_exit = True
    await serving
    await asyncio.sleep(0.5)
    gc.collect()  # 버려진 작업을 지금 거둔다


print("원격 측정:", "켬" if telemetry.otel_enabled else "끔")
asyncio.run(main(int(sys.argv[2])))
gc.collect()
for line, n in sorted(SEEN.items()):
    print(f"{n:3} {line}")
print("합계", sum(SEEN.values()))
# @ norun
