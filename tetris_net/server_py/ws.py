# -*- coding: utf-8 -*-
"""ws.py — WebSocket(RFC 6455) 을 표준 라이브러리만으로 구현한다.

`pip install` 이 필요 없다는 게 이 파일의 존재 이유다. 파이썬만 있으면 서버가 뜬다.
Go 의 ws.go 와 같은 일을 하고, 같은 테스트(RFC §1.3 예제·길이 3갈래·마스킹)를 통과한다.

다루지 않는 것: 확장(permessage-deflate), 서브프로토콜 협상, TLS(그건 앞단 nginx 몫이다).
"""
import asyncio
import base64
import hashlib
import json
import secrets
import struct
import urllib.parse

OP_CONT, OP_TEXT, OP_BINARY, OP_CLOSE, OP_PING, OP_PONG = 0x0, 0x1, 0x2, 0x8, 0x9, 0xA

# RFC 6455 §1.3 이 못 박아 둔 마법 문자열. 한 글자만 틀려도 브라우저가 연결을 거부한다.
GUID = '258EAFA5-E914-47DA-95CA-C5AB0DC85B11'

MAX_PAYLOAD = 1 << 20
_LIMIT = 1 << 20


def accept_key(key: str) -> str:
    """Sec-WebSocket-Key → Sec-WebSocket-Accept. base64(SHA1(key + GUID))."""
    return base64.b64encode(hashlib.sha1((key + GUID).encode()).digest()).decode()


def build_frame(op: int, payload: bytes, mask: bool = False, fin: bool = True) -> bytes:
    """프레임 한 개를 통째로 만든다. 머리와 본문을 나눠 쓰지 않는 게 중요하다 —
    작은 프레임이 두 세그먼트로 쪼개져 나가면 상대가 머리만 읽고 멈추는 일이 생긴다."""
    b0 = (0x80 if fin else 0) | (op & 0x0F)
    n = len(payload)
    mbit = 0x80 if mask else 0
    if n < 126:
        head = struct.pack('!BB', b0, mbit | n)
    elif n <= 0xFFFF:
        head = struct.pack('!BBH', b0, mbit | 126, n)
    else:
        head = struct.pack('!BBQ', b0, mbit | 127, n)
    if not mask:
        return head + payload
    key = secrets.token_bytes(4)
    return head + key + bytes(b ^ key[i & 3] for i, b in enumerate(payload))


class WSConn:
    """업그레이드가 끝난 연결 하나.

    client=True 면 방향이 뒤집힌다 — 보낼 때 마스킹하고, 받을 때 마스킹을 요구하지 않는다.
    (RFC 6455 §5.1: 클라이언트→서버는 반드시 마스킹, 서버→클라이언트는 절대 마스킹 금지)
    """

    def __init__(self, reader, writer, client=False, max_payload=MAX_PAYLOAD):
        self.reader, self.writer, self.client = reader, writer, client
        self.max_payload = max_payload
        self._wlock = asyncio.Lock()
        self._closed = False

    # ── 읽기 ──
    async def _read_frame(self):
        h = await self.reader.readexactly(2)
        if h[0] & 0x70:
            raise ValueError('RSV 비트가 켜져 있다 (확장을 협상한 적이 없다)')
        fin, op = bool(h[0] & 0x80), h[0] & 0x0F
        masked = bool(h[1] & 0x80)
        if not masked and not self.client:
            # 마스킹 요구는 보안이 아니라, 낡은 캐시 프록시가 본문을 HTTP 로
            # 오해하지 못하게 하려는 장치다.
            raise ValueError('마스킹되지 않은 클라이언트 프레임')
        if masked and self.client:
            raise ValueError('서버가 마스킹된 프레임을 보냈다')
        n = h[1] & 0x7F
        if n == 126:
            n = struct.unpack('!H', await self.reader.readexactly(2))[0]
        elif n == 127:
            n = struct.unpack('!Q', await self.reader.readexactly(8))[0]
        if n > self.max_payload:
            raise ValueError('프레임이 상한을 넘었다 (%d)' % n)
        key = await self.reader.readexactly(4) if masked else None
        data = await self.reader.readexactly(n) if n else b''
        if masked:
            data = bytes(b ^ key[i & 3] for i, b in enumerate(data))
        return fin, op, data

    async def recv(self):
        """조각난 프레임을 이어 붙여 메시지 하나를 돌려준다. 끝났으면 None.
        제어 프레임(핑/퐁/닫기)은 여기서 삼키고 애플리케이션에 올리지 않는다."""
        msg_op, buf = None, bytearray()
        while True:
            try:
                fin, op, data = await self._read_frame()
            except (asyncio.IncompleteReadError, ConnectionError, ValueError, OSError):
                return None
            if op & 0x8:                       # 제어 프레임
                if not fin or len(data) > 125:
                    return None
                if op == OP_PING:
                    await self.send(OP_PONG, data)
                elif op == OP_CLOSE:
                    await self.send(OP_CLOSE, data)
                    return None
                continue                        # 퐁은 살아 있다는 신호. 할 일 없음
            if op == OP_CONT:
                if msg_op is None:
                    return None
            else:
                if msg_op is not None:
                    return None
                msg_op = op
            buf += data
            if len(buf) > self.max_payload:
                return None
            if fin:
                return msg_op, bytes(buf)

    async def recv_json(self):
        m = await self.recv()
        if m is None:
            return None
        op, data = m
        if op != OP_TEXT:
            return {}
        try:
            return json.loads(data.decode('utf-8'))
        except (ValueError, UnicodeDecodeError):
            return {}

    # ── 쓰기 ──
    async def send(self, op, data: bytes):
        if self._closed:
            return
        async with self._wlock:                 # 프레임은 원자적으로 나가야 한다
            try:
                self.writer.write(build_frame(op, data, mask=self.client))
                await self.writer.drain()
            except (ConnectionError, OSError):
                self._closed = True

    async def send_text(self, s: str):
        await self.send(OP_TEXT, s.encode('utf-8'))

    async def send_json(self, obj):
        # ensure_ascii=False 로 보내야 한글 이름이 \uXXXX 로 부풀지 않는다.
        await self.send_text(json.dumps(obj, ensure_ascii=False, separators=(',', ':')))

    async def close(self):
        if self._closed:
            return
        self._closed = True
        try:
            self.writer.close()
            await self.writer.wait_closed()
        except (ConnectionError, OSError):
            pass


# ── 핸드셰이크 ──
def _parse_head(raw: bytes):
    lines = raw.decode('latin1').split('\r\n')
    parts = lines[0].split(' ')
    if len(parts) < 2:
        return None, '', {}
    headers = {}
    for line in lines[1:]:
        if ':' in line:
            k, v = line.split(':', 1)
            headers[k.strip().lower()] = v.strip()
    return parts[0], parts[1], headers


async def serve(handler, host, port, http=None):
    """웹소켓 서버를 연다. handler(conn, path) 가 연결 하나의 일생을 맡는다.
    업그레이드가 아닌 요청은 http(path) 에 넘긴다 — (상태, 콘텐츠타입, 본문) 또는 None."""

    async def on_client(reader, writer):
        try:
            raw = await asyncio.wait_for(reader.readuntil(b'\r\n\r\n'), 10)
        except (asyncio.TimeoutError, asyncio.IncompleteReadError, OSError,
                asyncio.LimitOverrunError):
            writer.close()
            return
        method, path, headers = _parse_head(raw)
        up = headers.get('upgrade', '').lower() == 'websocket'
        key = headers.get('sec-websocket-key', '')
        if method != 'GET' or not up or not key or headers.get('sec-websocket-version') != '13':
            status, ctype, body = (http(path) if http else None) or \
                (404, 'text/plain; charset=utf-8', '없는 경로다\n'.encode())
            writer.write(('HTTP/1.1 %d OK\r\nContent-Type: %s\r\nContent-Length: %d\r\n'
                          'Connection: close\r\n\r\n' % (status, ctype, len(body))).encode('latin1'))
            writer.write(body)
            try:
                await writer.drain()
            except OSError:
                pass
            writer.close()
            return
        writer.write(('HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\n'
                      'Connection: Upgrade\r\nSec-WebSocket-Accept: %s\r\n\r\n'
                      % accept_key(key)).encode('latin1'))
        await writer.drain()
        conn = WSConn(reader, writer)
        try:
            await handler(conn, path)
        finally:
            await conn.close()

    return await asyncio.start_server(on_client, host, port, limit=_LIMIT)


async def connect(url: str) -> WSConn:
    """클라이언트 쪽. 테스트와 운영 도구가 쓴다 — 40줄이면 된다."""
    u = urllib.parse.urlparse(url)
    reader, writer = await asyncio.open_connection(u.hostname, u.port or 80, limit=_LIMIT)
    key = base64.b64encode(secrets.token_bytes(16)).decode()
    path = u.path or '/'
    if u.query:
        path += '?' + u.query
    writer.write(('GET %s HTTP/1.1\r\nHost: %s\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n'
                  'Sec-WebSocket-Key: %s\r\nSec-WebSocket-Version: 13\r\n\r\n'
                  % (path, u.netloc, key)).encode('latin1'))
    await writer.drain()
    raw = await reader.readuntil(b'\r\n\r\n')
    lines = raw.decode('latin1').split('\r\n')
    if '101' not in lines[0]:
        writer.close()
        raise ConnectionError('업그레이드 거절: %s' % lines[0])
    _, _, headers = _parse_head(raw)
    if headers.get('sec-websocket-accept') != accept_key(key):
        writer.close()
        raise ConnectionError('Sec-WebSocket-Accept 가 맞지 않는다')
    return WSConn(reader, writer, client=True)
