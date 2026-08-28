# -*- coding: utf-8 -*-
"""test_server_lib.py — websockets 라이브러리판 서버를 검증한다.

이 파일이 시험하는 주장은 둘이다:
  1) 전송층을 라이브러리로 갈아 끼워도 hub.py·room.py 는 한 줄도 안 바뀐다
     — 그래서 test_server.py 의 통합 시나리오가 여기서도 그대로 통과해야 한다.
  2) 상호운용 — 클라이언트는 ws.py 의 **직접 구현** 을 그대로 쓴다.
     직접 구현 클라이언트가 라이브러리 서버에 붙으면, 양쪽 다 RFC 6455 를 지킨 것이다.

이 파일만은 외부 패키지(websockets)가 필요하다. `pip install websockets` 뒤에 돌 것.
"""
import asyncio
import json
import unittest
import urllib.request

import ws                          # 클라이언트 쪽은 직접 구현 그대로 쓴다
import server_lib
from hub import Hub, PROTO_VERSION
from server import make_http       # HTTP 경로 처리도 기존 서버 것을 그대로 재사용
from test_server import _read_frames


class TestLibServer(unittest.IsolatedAsyncioTestCase):
    """test_server.py 의 TestServer 와 같은 시나리오 — 서버만 라이브러리판이다."""

    async def asyncSetUp(self):
        self.hub = Hub()
        self.server = await server_lib.serve(self.hub.serve, '127.0.0.1', 0,
                                             http=make_http(self.hub, ''))
        self.port = self.server.sockets[0].getsockname()[1]
        self.conns = []

    async def asyncTearDown(self):
        for c in self.conns:
            await c.close()
        self.server.close()
        await self.server.wait_closed()

    async def dial(self):
        c = await ws.connect('ws://127.0.0.1:%d/ws' % self.port)
        self.conns.append(c)
        return c

    async def test_hello_version(self):
        """경계값 — 버전이 v-1 이면 err ver 를 받고 끊긴다."""
        c = await self.dial()
        await c.send_json({'t': 'hello', 'v': PROTO_VERSION - 1, 'name': '옛날'})
        m = (await _read_frames(c, ['err']))['err']
        self.assertEqual('ver', m['code'])

    async def test_ping(self):
        c = await self.dial()
        await c.send_json({'t': 'hello', 'v': PROTO_VERSION, 'name': 'x'})
        await _read_frames(c, ['hi'])
        await c.send_json({'t': 'ping', 'c': 42})
        self.assertEqual(42, (await _read_frames(c, ['pong']))['pong']['c'])

    async def test_join_unknown(self):
        c = await self.dial()
        await c.send_json({'t': 'hello', 'v': PROTO_VERSION, 'name': 'x'})
        await _read_frames(c, ['hi'])
        await c.send_json({'t': 'join', 'room': 'ZZZZZZ'})
        self.assertEqual('nosuch', (await _read_frames(c, ['err']))['err']['code'])

    async def test_create_join_and_play(self):
        """PC 2대 × 2석 = 4인 — 시드 합의와 가비지 중계까지 test_server.py 와 동일."""
        a, b = await self.dial(), await self.dial()
        await a.send_json({'t': 'hello', 'v': PROTO_VERSION, 'name': '보라'})
        await _read_frames(a, ['hi'])
        await a.send_json({'t': 'create', 'cfg': {'max': 4, 'target': 'random'}})
        code = (await _read_frames(a, ['joined']))['joined']['code']
        self.assertEqual(6, len(code))

        await b.send_json({'t': 'hello', 'v': PROTO_VERSION, 'name': '다온'})
        await _read_frames(b, ['hi'])
        await b.send_json({'t': 'join', 'room': code})
        await _read_frames(b, ['joined'])

        for k, (conn, who) in enumerate(((a, '보라'), (b, '다온'))):
            await conn.send_json({'t': 'seat', 'i': k * 2, 'kind': 'human', 'name': who})
            await conn.send_json({'t': 'seat', 'i': k * 2 + 1, 'kind': 'ai', 'name': '봇', 'lv': 'hard'})
            await conn.send_json({'t': 'ready', 'v': True})

        async def wait_ready():
            while True:
                m = await a.recv_json()
                if m and m.get('t') == 'room' and len(m['seats']) == 4:
                    if all(s['ready'] for s in m['seats'] if s['kind'] == 'human'):
                        return m
        await asyncio.wait_for(wait_ready(), 4)

        await a.send_json({'t': 'start'})
        sa = (await _read_frames(a, ['start']))['start']
        sb = (await _read_frames(b, ['start']))['start']
        self.assertEqual(sa['seed'], sb['seed'], '두 PC 가 같은 시드를 받아야 한다')

        await a.send_json({'t': 'atk', 'i': 0, 'n': 4})
        ga = (await _read_frames(a, ['grb']))['grb']
        gb = (await _read_frames(b, ['grb']))['grb']
        self.assertEqual(ga, gb, '관전용으로 두 PC 가 같은 grb 를 본다')
        self.assertEqual(4, ga['n'])

    async def test_peer_drop_kills_seats(self):
        """재진입 — 판 도중 PC 하나가 사라지면 그 좌석들이 KO 처리되는가."""
        a, b = await self.dial(), await self.dial()
        await a.send_json({'t': 'hello', 'v': PROTO_VERSION, 'name': 'A'})
        await _read_frames(a, ['hi'])
        await a.send_json({'t': 'create', 'cfg': {'max': 4}})
        code = (await _read_frames(a, ['joined']))['joined']['code']
        await b.send_json({'t': 'hello', 'v': PROTO_VERSION, 'name': 'B'})
        await _read_frames(b, ['hi'])
        await b.send_json({'t': 'join', 'room': code})
        await _read_frames(b, ['joined'])
        await a.send_json({'t': 'seat', 'i': 0, 'kind': 'ai', 'name': 'A'})
        await b.send_json({'t': 'seat', 'i': 1, 'kind': 'ai', 'name': 'B'})
        await asyncio.sleep(0.15)
        await a.send_json({'t': 'start'})
        await _read_frames(a, ['start'])
        await b.close()
        got = await _read_frames(a, ['ko', 'end'])
        self.assertEqual(1, got['ko']['i'])
        self.assertEqual([0, 1], got['end']['order'])

    async def test_http_endpoints(self):
        """업그레이드가 아닌 요청 — process_request 가 make_http 로 위임하는가."""
        def get(path):
            req = urllib.request.urlopen('http://127.0.0.1:%d%s' % (self.port, path), timeout=4)
            return req.status, req.read()
        st, body = await asyncio.to_thread(get, '/healthz')
        self.assertEqual((200, b'ok'), (st, body))
        st, body = await asyncio.to_thread(get, '/rooms')
        self.assertEqual(200, st)
        self.assertEqual(PROTO_VERSION, json.loads(body)['v'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
