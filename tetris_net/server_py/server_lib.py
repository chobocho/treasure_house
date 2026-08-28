#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""server_lib.py — websockets 라이브러리판 서버.

ws.py(234줄)가 하던 일 — 핸드셰이크·프레임 코덱·HTTP 겸용 대응 — 을 전부
websockets 라이브러리에 맡긴다. hub.py·room.py 는 한 줄도 바꾸지 않는다:
Hub 가 연결에 요구하는 말은 recv_json / send_text / close 세 마디뿐이라,
라이브러리 연결을 그 세 마디로 감싼 어댑터(LibConn)만 있으면 된다.

직접 구현(ws.py)과 다른 점은 공짜로 얻는 것들이다 — close 코드 협상,
20초 간격 keepalive ping, 조각난 프레임 조립, 읽기 상한. 대신
"파이썬만 있으면 돈다"는 깨진다:  pip install websockets  가 먼저다.

    python3 server_lib.py --port 8787 --dir ../web
"""
import argparse
import asyncio
import json
import signal
import sys

import websockets
from websockets.asyncio.server import serve as _lib_serve
from websockets.datastructures import Headers
from websockets.http11 import Response

from hub import Hub, PROTO_VERSION
from server import make_http           # /healthz·/rooms·정적 파일 규칙을 그대로 재사용


class LibConn:
    """Hub 가 아는 연결의 세 마디로 라이브러리 연결을 감싼다. 이 클래스가 어댑터의 전부다."""

    def __init__(self, conn):
        self._c = conn

    async def recv_json(self):
        # ws.py 와 같은 계약 — 닫혔으면 None, 텍스트가 아니거나 JSON 이 아니면 {}.
        # 제어 프레임(ping/close)은 라이브러리가 알아서 삼키므로 여기 도착하지 않는다.
        try:
            m = await self._c.recv()
        except websockets.ConnectionClosed:
            return None
        if isinstance(m, bytes):
            return {}
        try:
            return json.loads(m)
        except ValueError:
            return {}

    async def send_text(self, s):
        try:
            await self._c.send(s)
        except websockets.ConnectionClosed:
            pass                           # 죽은 연결 정리는 recv 쪽이 맡는다

    async def close(self):
        await self._c.close()


def _process_request(http):
    """업그레이드가 아닌 요청 → 기존 make_http 핸들러로 위임한다.
    ws.py 의 serve 가 손으로 하던 분기를 라이브러리는 훅 하나로 연다."""
    def handle(conn, request):
        if request.headers.get('Upgrade', '').lower() == 'websocket':
            return None                    # 진짜 웹소켓 — 핸드셰이크를 계속 진행한다
        status, ctype, body = (http(request.path) if http else None) or \
            (404, 'text/plain; charset=utf-8', '없는 경로다\n'.encode())
        return Response(status, 'OK', Headers([
            ('Content-Type', ctype), ('Content-Length', str(len(body)))]), body)
    return handle


async def serve(handler, host, port, http=None):
    """ws.serve 와 같은 시그니처. 그래서 server.py 의 실행 로직이 그대로 옮겨 온다."""
    async def on_conn(conn):
        await handler(LibConn(conn), conn.request.path)
    return await _lib_serve(on_conn, host, port,
                            process_request=_process_request(http),
                            max_size=64 << 10)   # hub 가 ws.py 판에서 걸던 상한과 같다


async def main_async(args):
    hub = Hub()
    server = await serve(hub.serve, args.host, args.port, http=make_http(hub, args.dir))
    addr = server.sockets[0].getsockname()
    print('듣는 중: %s:%d (프로토콜 v%d, websockets %s)'
          % (addr[0], addr[1], PROTO_VERSION, websockets.__version__), flush=True)

    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, stop.set)
        except NotImplementedError:        # 윈도우에는 add_signal_handler 가 없다
            signal.signal(sig, lambda *_: stop.set())
    await stop.wait()
    print('종료 신호를 받았다 — 새 연결을 막는다', flush=True)
    server.close()
    await server.wait_closed()


def main(argv=None):
    ap = argparse.ArgumentParser(description='테트리스 8인 대전 서버 (파이썬 · websockets 라이브러리판)')
    ap.add_argument('--host', default='0.0.0.0')
    ap.add_argument('--port', type=int, default=8787)
    ap.add_argument('--dir', default='', help='같이 내줄 정적 파일 디렉터리')
    args = ap.parse_args(argv)
    try:
        asyncio.run(main_async(args))
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == '__main__':
    sys.exit(main())
