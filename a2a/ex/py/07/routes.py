# 라우트 팩토리 셋은 Starlette Route 의 목록을 만들 뿐이다 —
# 무엇이 생기나.
#   python 07/routes.py
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import (
    create_agent_card_routes,
    create_jsonrpc_routes,
    create_rest_routes,
)
from a2a.server.tasks import InMemoryTaskStore
from step1_echo import EchoExecutor, card

agent_card = card("http://127.0.0.1:10700/")
handler = DefaultRequestHandler(
    agent_executor=EchoExecutor(),
    task_store=InMemoryTaskStore(),
    agent_card=agent_card,
)


# region: routes
def show(title, routes):
    print(f"{title} → {len(routes)}개")
    for r in routes:
        if not hasattr(r, "methods"):  # Mount — 아래에 경로를 또 단다
            print(f"  (Mount)  {r.path} 아래에 같은 {len(r.routes)}개")
            continue
        methods = ",".join(sorted(r.methods - {"HEAD"}))
        print(f"  {methods:<7}{r.path}")


show(
    "create_agent_card_routes(card)",
    create_agent_card_routes(agent_card),
)
show(
    "create_jsonrpc_routes(h, '/')", create_jsonrpc_routes(handler, "/")
)
show("create_rest_routes(h)", create_rest_routes(handler))
# endregion
