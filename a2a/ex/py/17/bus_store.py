"""교통 에이전트를 파일 저장소로 — 실행기·카드는 agents/bus.py 의 것.

    python 17/bus_store.py --port P [--step-ms N] [--dir D] [--recover]

--dir 을 주지 않으면 $TMPDIR/tasks-P (실행 명세마다 새로 비는 곳).
"""

import argparse
import asyncio
import os
import tempfile

import httpx
import uvicorn
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import (
    create_agent_card_routes,
    create_jsonrpc_routes,
)
from a2a.server.tasks import (
    BasePushNotificationSender,
    InMemoryPushNotificationConfigStore,
)
from filestore import FileTaskStore
from starlette.applications import Starlette

from agents.bus import BusExecutor, card

p = argparse.ArgumentParser(
    description="파일 저장소를 쓰는 교통 에이전트"
)
p.add_argument("--port", type=int, required=True)
p.add_argument("--step-ms", type=int, default=300)
p.add_argument("--dir")
p.add_argument("--recover", action="store_true")
args = p.parse_args()
folder = args.dir or os.path.join(
    tempfile.gettempdir(), f"tasks-{args.port}"
)
url = f"http://127.0.0.1:{args.port}/"

# region: wire
store = FileTaskStore(folder)  # Task 만 디스크로
if args.recover:
    asyncio.run(store.recover())
pushes = (
    InMemoryPushNotificationConfigStore()
)  # 푸시 설정은 메모리 그대로
handler = DefaultRequestHandler(
    agent_executor=BusExecutor(args.step_ms),
    task_store=store,
    agent_card=card(url),
    push_config_store=pushes,
    push_sender=BasePushNotificationSender(httpx.AsyncClient(), pushes),
)
# endregion
app = Starlette(
    routes=[
        *create_agent_card_routes(card(url)),
        *create_jsonrpc_routes(handler, "/"),
    ]
)
uvicorn.run(app, host="127.0.0.1", port=args.port, log_level="warning")
# @ norun
