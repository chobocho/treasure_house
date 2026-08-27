# -*- coding: utf-8 -*-
"""test_server.py — 파이썬 서버 3층을 전부 검증한다.

  1) room.py   : Go·JS 와 **같은 골든 벡터**를 그대로 재현하는가
  2) ws.py     : RFC 6455 프레임을 옳게 만들고 읽는가
  3) hub+server: 진짜 소켓으로 붙어 진짜 한 판이 도는가

표준 라이브러리만 쓴다. 외부 패키지를 하나라도 넣는 순간 "파이썬만 있으면 돈다"가 깨진다.
"""
import asyncio
import io
import json
import os
import unittest

import ws
import room as roommod
from hub import Hub

HERE = os.path.dirname(os.path.abspath(__file__))
VEC = json.load(io.open(os.path.join(HERE, '..', 'protocol_vectors.json'), encoding='utf-8'))


class TestGoldenVectors(unittest.TestCase):
    """골든 벡터 — 세 구현이 갈리는 지점을 잡는 유일한 장치다."""

    def test_vectors(self):
        self.assertEqual(VEC['v'], 3)
        for c in VEC['cases']:
            with self.subTest(case=c['name']):
                r = roommod.Room(c.get('cfg') or {}, c['seed'])
                for s in c['setup']:
                    r.handle(s['pid'], s['m'], int(s.get('at', 0)))
                for k, s in enumerate(c['steps'], 1):
                    got = r.handle(s['pid'], s['m'], int(s.get('at', 0)))
                    want = [(o['to'], o['m']) for o in s['out']]
                    self.assertEqual(want, got,
                                     '%s #%d(%s)' % (c['name'], k, c['why']))

    def test_xorshift32(self):
        r = roommod.Room({}, 1)
        self.assertEqual([270369, 67634689, 2647435461, 307599695, 2398689233],
                         [r.rng() for _ in range(5)])

    def test_eight_seats_four_peers(self):
        """요구사항 그대로의 최대 구성 — PC 4대 × 2석 = 8석"""
        r = roommod.Room({'max': 8, 'perPeer': 2}, 1)
        for pid in range(1, 5):
            r.handle(pid, {'t': 'seat', 'i': -1, 'kind': 'human', 'name': 'a'}, 0)
            r.handle(pid, {'t': 'seat', 'i': -1, 'kind': 'ai', 'name': 'b', 'lv': 'hard'}, 0)
            r.handle(pid, {'t': 'ready', 'v': True}, 0)
        out = r.handle(1, {'t': 'start'}, 0)
        self.assertEqual(1, len(out))
        seats = out[0][1]['seats']
        self.assertEqual(8, len(seats))
        self.assertEqual([1, 1, 2, 2, 3, 3, 4, 4], [s['pid'] for s in seats])
        self.assertEqual([(5, {'t': 'err', 'code': 'phase'})],
                         r.handle(5, {'t': 'seat', 'i': -1, 'kind': 'human', 'name': 'x'}, 0))


class TestFrames(unittest.TestCase):
    """RFC 6455 — 프레임은 바이트 배열 문제이지 통신 문제가 아니다."""

    def test_accept_key(self):
        # RFC 6455 §1.3 의 예제 그대로
        self.assertEqual('s3pPLMBiTxaQ9kYGzzhZRbK+xOo=', ws.accept_key('dGhlIHNhbXBsZSBub25jZQ=='))

    def test_server_frame_unmasked(self):
        f = ws.build_frame(ws.OP_TEXT, '안녕'.encode(), mask=False)
        self.assertEqual(0x81, f[0])          # FIN + text
        self.assertEqual(0, f[1] & 0x80)      # 서버는 마스킹하지 않는다
        self.assertEqual('안녕'.encode(), f[2:])

    def test_length_forms(self):
        for n, hdr in ((0, 2), (125, 2), (126, 4), (65535, 4), (65536, 10)):
            f = ws.build_frame(ws.OP_BINARY, b'x' * n, mask=False)
            self.assertEqual(hdr + n, len(f), '%d바이트' % n)

    def test_mask_roundtrip(self):
        payload = 'ㅁㄴㅇㄹ 8인'.encode()
        f = ws.build_frame(ws.OP_TEXT, payload, mask=True)
        self.assertEqual(0x80, f[1] & 0x80)
        key = f[2:6]
        got = bytes(b ^ key[i & 3] for i, b in enumerate(f[6:]))
        self.assertEqual(payload, got)


async def _read_frames(conn, kinds, timeout=4.0):
    """원하는 t 가 나올 때까지 읽는다. 다른 메시지는 흘려보낸다."""
    want = list(kinds)
    got = {}
    async def run():
        while want:
            m = await conn.recv_json()
            if m is None:
                raise AssertionError('연결이 끊겼다 (남은 기대: %s)' % want)
            if m.get('t') in want:
                want.remove(m['t'])
                got[m['t']] = m
    await asyncio.wait_for(run(), timeout)
    return got


class TestServer(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.hub = Hub()
        self.server = await ws.serve(self.hub.serve, '127.0.0.1', 0)
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
        c = await self.dial()
        await c.send_json({'t': 'hello', 'v': 2, 'name': '옛날'})
        m = (await _read_frames(c, ['err']))['err']
        self.assertEqual('ver', m['code'])

    async def test_ping(self):
        c = await self.dial()
        await c.send_json({'t': 'hello', 'v': 3, 'name': 'x'})
        await _read_frames(c, ['hi'])
        await c.send_json({'t': 'ping', 'c': 42})
        self.assertEqual(42, (await _read_frames(c, ['pong']))['pong']['c'])

    async def test_join_unknown(self):
        c = await self.dial()
        await c.send_json({'t': 'hello', 'v': 3, 'name': 'x'})
        await _read_frames(c, ['hi'])
        await c.send_json({'t': 'join', 'room': 'ZZZZZZ'})
        self.assertEqual('nosuch', (await _read_frames(c, ['err']))['err']['code'])

    async def test_create_join_and_play(self):
        """PC 2대 × 2석 = 4인. 서버가 골라 준 타겟으로 가비지가 흐르는지까지."""
        a, b = await self.dial(), await self.dial()
        await a.send_json({'t': 'hello', 'v': 3, 'name': '보라'})
        await _read_frames(a, ['hi'])
        await a.send_json({'t': 'create', 'cfg': {'max': 4, 'target': 'random'}})
        code = (await _read_frames(a, ['joined']))['joined']['code']
        self.assertEqual(6, len(code))

        await b.send_json({'t': 'hello', 'v': 3, 'name': '다온'})
        await _read_frames(b, ['hi'])
        await b.send_json({'t': 'join', 'room': code})
        await _read_frames(b, ['joined'])

        for k, (conn, who) in enumerate(((a, '보라'), (b, '다온'))):
            await conn.send_json({'t': 'seat', 'i': k * 2, 'kind': 'human', 'name': who})
            await conn.send_json({'t': 'seat', 'i': k * 2 + 1, 'kind': 'ai', 'name': '봇', 'lv': 'hard'})
            await conn.send_json({'t': 'ready', 'v': True})

        # 좌석 4석이 전부 준비될 때까지 기다린다
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
        self.assertEqual(0, ga['from'])
        self.assertEqual(4, ga['n'])
        self.assertIn(ga['hole'], range(10))

    async def test_peer_drop_kills_seats(self):
        a, b = await self.dial(), await self.dial()
        await a.send_json({'t': 'hello', 'v': 3, 'name': 'A'})
        await _read_frames(a, ['hi'])
        await a.send_json({'t': 'create', 'cfg': {'max': 4}})
        code = (await _read_frames(a, ['joined']))['joined']['code']
        await b.send_json({'t': 'hello', 'v': 3, 'name': 'B'})
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


if __name__ == '__main__':
    unittest.main(verbosity=2)
