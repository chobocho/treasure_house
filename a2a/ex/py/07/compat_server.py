# 견적 에이전트(2단계)를 v0.3 호환 스위치를 켜고/끄고 띄운다.
#   python 07/compat_server.py --port P [--url U] [--compat]
import argparse

import uvicorn
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import (
    create_agent_card_routes,
    create_jsonrpc_routes,
)
from a2a.server.tasks import InMemoryTaskStore
from starlette.applications import Starlette
from step2_task import QuoteExecutor, card


# region: serve
def main():
    p = argparse.ArgumentParser()
    p.add_argument("--port", type=int, required=True)
    p.add_argument("--url")
    p.add_argument("--compat", action="store_true")
    args = p.parse_args()
    agent_card = card(args.url or f"http://127.0.0.1:{args.port}/")
    handler = DefaultRequestHandler(
        agent_executor=QuoteExecutor(),
        task_store=InMemoryTaskStore(),
        agent_card=agent_card,
    )
    routes = create_agent_card_routes(agent_card)
    routes += create_jsonrpc_routes(
        handler,
        "/",
        enable_v0_3_compat=args.compat,  # 스위치 하나
    )
    app = Starlette(routes=routes)
    uvicorn.run(
        app, host="127.0.0.1", port=args.port, log_level="warning"
    )


# endregion

if __name__ == "__main__":
    main()
# @ norun
