# -*- coding: utf-8 -*-
"""hub.py — 방 코드·연결·중계. 게임 규칙은 한 줄도 여기 없다 (전부 room.py 에 있다).

Go 판(hub.go)과 동시성 모델이 다른 게 재미있는 부분이다.
  * Go  : 방마다 고루틴 하나를 두고 채널로 직렬화했다. Room 에 뮤텍스가 없는 이유.
  * 여기: `Room.handle` 이 **동기 함수**다. asyncio 는 await 지점에서만 양보하므로
          handle 이 도는 동안 다른 코루틴이 끼어들 수 없다 — 그 자체로 원자적이다.
          그래서 방 전용 태스크도, 락도 필요 없다.
느린 클라이언트 대책만 Go 와 똑같이 둔다: PC 마다 보낼 큐 하나 + 쓰기 태스크 하나,
큐가 넘치면 기다리지 않고 끊는다.
"""
import asyncio
import json
import secrets
import time

from room import Room, DEFAULTS

PROTO_VERSION = 3
CODE_ALPHABET = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'   # 0/O, 1/I/L 처럼 헷갈리는 글자는 뺐다


class Peer:
    """PC 1대. 좌석은 최대 2석까지 이 안에 들어간다."""

    def __init__(self, pid, conn):
        self.pid = pid
        self.conn = conn
        self.name = ''
        self.rh = None
        self.greeted = False
        self.q = asyncio.Queue(maxsize=64)
        self.dead = False
        self.task = asyncio.create_task(self._writer())

    async def _writer(self):
        try:
            while True:
                m = await self.q.get()
                if m is None:
                    return
                await self.conn.send_text(m)
        except asyncio.CancelledError:
            pass

    def push(self, obj):
        if self.dead:
            return
        try:
            self.q.put_nowait(json.dumps(obj, ensure_ascii=False, separators=(',', ':')))
        except asyncio.QueueFull:
            # 이 PC 가 우리 속도를 못 따라온다. 기다려 주면 방 전체가 멈춘다.
            self.dead = True
            asyncio.create_task(self.conn.close())

    async def finish(self):
        """우아한 종료 — 큐를 다 비운 뒤에 닫는다.
        '버전이 안 맞는다' 같은 마지막 한 마디가 이 순서 덕분에 도착한다."""
        if not self.dead:
            self.dead = True
            try:
                self.q.put_nowait(None)
            except asyncio.QueueFull:
                self.task.cancel()
        await asyncio.sleep(0)


class RoomHost:
    def __init__(self, code, cfg):
        self.code = code
        self.cfg = cfg
        self.room = Room(cfg, secrets.randbits(31) | 1)
        self.peers = {}
        self.t0 = time.monotonic()

    def now(self):
        return int((time.monotonic() - self.t0) * 1000)

    def dispatch(self, outs):
        for to, m in outs:
            if to == 0:
                for p in self.peers.values():
                    p.push(m)
            elif to in self.peers:
                self.peers[to].push(m)


class Hub:
    def __init__(self):
        self.rooms = {}
        self.next_pid = 0

    def new_code(self):
        while True:
            code = ''.join(secrets.choice(CODE_ALPHABET) for _ in range(6))
            if code not in self.rooms:
                return code

    def create_room(self, cfg):
        rh = RoomHost(self.new_code(), cfg)
        self.rooms[rh.code] = rh
        return rh

    def stats(self):
        return [{'code': c, 'age': int(time.monotonic() - rh.t0)} for c, rh in self.rooms.items()]

    async def serve(self, conn, path):
        """연결 하나의 일생. ws.serve 가 연결마다 이 코루틴을 하나씩 띄운다."""
        self.next_pid += 1
        p = Peer(self.next_pid, conn)
        try:
            while True:
                m = await conn.recv_json()
                if m is None:
                    break
                t = m.get('t')
                if t == 'hello':
                    if m.get('v') != PROTO_VERSION:
                        p.push({'t': 'err', 'code': 'ver'})
                        break
                    p.name, p.greeted = m.get('name') or '', True
                    p.push({'t': 'hi', 'pid': p.pid, 'v': PROTO_VERSION})
                elif not p.greeted:
                    p.push({'t': 'err', 'code': 'hello'})
                elif t == 'ping':
                    p.push({'t': 'pong', 'c': m.get('c')})
                elif t in ('create', 'join'):
                    if p.rh is not None:
                        p.push({'t': 'err', 'code': 'inroom'})
                        continue
                    if t == 'create':
                        rh = self.create_room(merge_cfg(m.get('cfg') or {}))
                    else:
                        rh = self.rooms.get(m.get('room') or '')
                        if rh is None:
                            p.push({'t': 'err', 'code': 'nosuch'})
                            continue
                    p.rh = rh
                    p.push({'t': 'joined', 'code': rh.code, 'cfg': rh.cfg, 'pid': p.pid})
                    rh.peers[p.pid] = p
                elif p.rh is None:
                    p.push({'t': 'err', 'code': 'nosuch'})
                else:
                    p.rh.dispatch(p.rh.room.handle(p.pid, m, p.rh.now()))
        finally:
            if p.rh is not None:
                rh = p.rh
                rh.dispatch(rh.room.handle(p.pid, {'t': 'bye'}, rh.now()))
                rh.peers.pop(p.pid, None)
                if not rh.peers:
                    self.rooms.pop(rh.code, None)   # 아무도 없는 방은 사라진다
            await p.finish()


def merge_cfg(inc):
    """클라이언트가 안 적은 칸은 기본값을 그대로 둔다."""
    cfg = dict(DEFAULTS)
    for k in cfg:
        v = inc.get(k)
        if isinstance(v, bool) or v is None:
            continue
        if isinstance(v, (int, float)) and v > 0:
            cfg[k] = int(v)
        elif isinstance(v, str) and v:
            cfg[k] = v
    cfg['max'] = max(1, min(8, cfg['max']))
    return cfg
