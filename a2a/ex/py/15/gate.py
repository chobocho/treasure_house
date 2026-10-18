"""동시 위임을 시험하는 관문 — 동료 셋 앞에 서서 요청을 붙잡는다.

    python 15/gate.py 이름=듣는포트:보낼포트 …   (적은 차례 = 놓는 차례)

SendMessage(POST)는 셋이 모두 들어올 때까지 붙잡는다. 기획 에이전트가
하나씩 차례로 맡긴다면 둘째 요청은 오지 않고 10초 뒤 504 로 끝난다.
셋이 모이면 적은 차례대로 하나씩 넘기고, 앞의 응답을 다 돌려준 뒤에
다음 것을 넘긴다 — 기획 에이전트가 받는 응답의 도착 순서를 이쪽이
정하는 것이다. 카드 GET 은 붙잡지 않고 그냥 넘긴다.
"""

import asyncio
import socket
import sys

import httpx
import uvicorn
from starlette.applications import Starlette
from starlette.background import BackgroundTask
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Route

ROUTES = {}  # 듣는 포트 → (이름, 보낼 포트)
for arg in sys.argv[1:]:
    name, _, ports = arg.partition("=")
    listen, _, target = ports.partition(":")
    ROUTES[int(listen)] = (name, int(target))
ORDER = [name for name, _ in ROUTES.values()]
held = {}  # 이번 판에 붙잡힌 요청: 이름 → (차례, 끝남)
SKIP = {"host", "content-length"}


# region: hold
async def release(round_):
    """적은 차례대로 하나씩 놓는다. 앞의 응답이 나간 뒤에 다음 것."""
    for name in ORDER:
        turn, done = round_[name]
        turn.set()
        await done.wait()


async def relay(req: Request):
    # Host 머리글이 아니라 실제로 받은 소켓의 포트로 가른다
    name, target = ROUTES[req.scope["server"][1]]
    done = asyncio.Event()
    if req.method == "POST":
        turn = asyncio.Event()
        held[name] = (turn, done)
        if len(held) == len(ORDER):
            print(
                f"[관문] {len(held)}건이 동시에 열렸습니다", flush=True
            )
            asyncio.create_task(release(dict(held)))
            held.clear()
        try:
            await asyncio.wait_for(turn.wait(), 10)
        except TimeoutError:
            print(f"[관문] {name}: 10초 동안 혼자였습니다", flush=True)
            return Response(status_code=504)
        print(f"[관문] {name} 요청을 넘깁니다", flush=True)
    # endregion
    head = {k: v for k, v in req.headers.items() if k not in SKIP}
    async with httpx.AsyncClient(timeout=30) as http:
        r = await http.request(
            req.method,
            f"http://127.0.0.1:{target}{req.url.path}",
            content=await req.body(),
            headers=head,
        )
    # 응답이 다 나간 뒤에야 다음 차례를 놓는다(BackgroundTask)
    return Response(
        r.content,
        r.status_code,
        media_type=r.headers.get("content-type"),
        background=BackgroundTask(done.set),
    )


async def main():
    app = Starlette(
        routes=[Route("/{path:path}", relay, methods=["GET", "POST"])]
    )
    socks = []  # 서버 하나가 포트 셋을 함께 듣는다
    for port in ROUTES:
        s = socket.socket()
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(("127.0.0.1", port))
        socks.append(s)
    config = uvicorn.Config(app, log_level="warning")
    await uvicorn.Server(config).serve(sockets=socks)


asyncio.run(main())
# @ norun
