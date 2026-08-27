#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""server.py — 파이썬 서버 실행 파일. 표준 라이브러리만 쓴다.

    python3 server.py --port 8787 --dir ../web

Go 판(main.go)과 같은 프로토콜·같은 규칙이다. 다른 건 언어뿐이고,
같은 골든 벡터를 통과하므로 클라이언트는 어느 쪽에 붙어도 차이를 느끼지 못한다.
"""
import argparse
import asyncio
import json
import mimetypes
import os
import signal
import sys

import ws
from hub import Hub, PROTO_VERSION


def make_http(hub, static_dir):
    """업그레이드가 아닌 요청을 처리한다. (상태, 콘텐츠타입, 본문) 또는 None."""
    def handler(path):
        p = path.split('?', 1)[0]
        if p == '/healthz':
            return 200, 'text/plain; charset=utf-8', b'ok'
        if p == '/rooms':
            body = json.dumps({'v': PROTO_VERSION, 'rooms': hub.stats()},
                              ensure_ascii=False).encode('utf-8')
            return 200, 'application/json; charset=utf-8', body
        if not static_dir:
            return 200, 'text/plain; charset=utf-8', '테트리스 8인 대전 서버 v3 — 웹소켓은 /ws\n'.encode()
        # 정적 파일. `..` 로 디렉터리를 빠져나가려는 경로는 실경로를 비교해 막는다.
        rel = p.lstrip('/') or 'index.html'
        full = os.path.realpath(os.path.join(static_dir, rel))
        root = os.path.realpath(static_dir)
        if not full.startswith(root + os.sep) and full != root:
            return 403, 'text/plain; charset=utf-8', b'no'
        if os.path.isdir(full):
            full = os.path.join(full, 'index.html')
        if not os.path.isfile(full):
            return None
        ctype = mimetypes.guess_type(full)[0] or 'application/octet-stream'
        if ctype.startswith('text/') or ctype in ('application/javascript', 'application/json'):
            ctype += '; charset=utf-8'
        with open(full, 'rb') as f:
            return 200, ctype, f.read()
    return handler


async def main_async(args):
    hub = Hub()
    server = await ws.serve(hub.serve, args.host, args.port, http=make_http(hub, args.dir))
    addr = server.sockets[0].getsockname()
    print('듣는 중: %s:%d (프로토콜 v%d)' % (addr[0], addr[1], PROTO_VERSION), flush=True)

    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, stop.set)
        except NotImplementedError:      # 윈도우에는 add_signal_handler 가 없다
            signal.signal(sig, lambda *_: stop.set())
    await stop.wait()
    print('종료 신호를 받았다 — 새 연결을 막는다', flush=True)
    server.close()
    await server.wait_closed()


def main(argv=None):
    ap = argparse.ArgumentParser(description='테트리스 8인 대전 서버 (파이썬)')
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
