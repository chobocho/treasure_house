# -*- coding: utf-8 -*-
"""저장·리플레이·압축 (SPEC §20).

   리플레이는 **명령 로그**다. 상태는 한 바이트도 저장하지 않는다. 재생한다는
   것은 같은 시드로 시뮬을 새로 만들어 같은 명령을 같은 틱에 먹이는 것이고,
   결과가 같다는 증명은 `hashes.txt` 와의 대조가 대신한다. 1200틱 게임의
   리플레이가 수백 바이트인 것과 상태 스냅샷이 틱당 4 KB 인 것을 20부가
   나란히 놓는다.

   비트 연산자는 쓰지 않는다(§1.1). LZSS 의 토큰도 곱셈과 나눗셈으로 접는다.
"""

from . import fixed as F

MAGIC = b'RTSR'
VERSION = 1
WINDOW, MIN_MATCH, MAX_MATCH = 4096, 3, 18


def _b2(out, v):
    v %= 65536
    out.append(v // 256)
    out.append(v % 256)


def _b4(out, v):
    v %= 4294967296
    _b2(out, v // 65536)
    _b2(out, v % 65536)


def _r2(b, i):
    return b[i] * 256 + b[i + 1], i + 2


def _r4(b, i):
    hi, i = _r2(b, i)
    lo, i = _r2(b, i)
    return hi * 65536 + lo, i


# ── SPEC §20.2 ──────────────────────────────────────────────────────────────
def save(seed, players, ticks, log):
    """log 는 (틱, 명령 목록). 명령은 §18.1 의 여섯 칸이다."""
    out = bytearray()
    out += MAGIC
    out.append(VERSION)
    _b4(out, seed)
    out.append(players)
    _b4(out, ticks)
    _b2(out, len(log))
    for (t, orders) in sorted(log):
        _b4(out, t)
        out.append(len(orders))
        for (p, issuer, kind, a, b, c) in orders:
            out.append(p)
            out.append(kind)
            _b2(out, issuer)
            out.append(a)
            out.append(b)
            _b2(out, c)
    crc = F.crc16(bytes(out))
    _b2(out, crc)
    return bytes(out)


def load(blob):
    b = bytearray(blob)
    if bytes(b[:4]) != MAGIC:
        raise ValueError('리플레이 파일이 아니다')
    want = b[-2] * 256 + b[-1]
    if F.crc16(bytes(b[:-2])) != want:
        raise ValueError('CRC 불일치 — 리플레이가 깨졌다')
    i = 5
    seed, i = _r4(b, i)
    players = b[i]
    i += 1
    ticks, i = _r4(b, i)
    n, i = _r2(b, i)
    log = []
    for _k in range(n):
        t, i = _r4(b, i)
        cnt = b[i]
        i += 1
        orders = []
        for _j in range(cnt):
            p = b[i]
            kind = b[i + 1]
            issuer, i2 = _r2(b, i + 2)
            a = b[i2]
            bb = b[i2 + 1]
            c, i = _r2(b, i2 + 2)
            orders.append((p, issuer, kind, a, bb, c))
        log.append((t, orders))
    return seed, players, ticks, log


# ── SPEC §20.3 RLE ──────────────────────────────────────────────────────────
def rle_encode(data):
    """(개수, 값) 쌍. 개수는 1..255 — 넘으면 쌍을 나눈다."""
    out = bytearray()
    b = bytearray(data)
    i = 0
    while i < len(b):
        v = b[i]
        run = 1
        while i + run < len(b) and b[i + run] == v and run < 255:
            run += 1
        out.append(run)
        out.append(v)
        i += run
    return bytes(out)


def rle_decode(data):
    out = bytearray()
    b = bytearray(data)
    i = 0
    while i < len(b):
        for _k in range(b[i]):
            out.append(b[i + 1])
        i += 2
    return bytes(out)


# ── SPEC §20.4 LZSS ─────────────────────────────────────────────────────────
def _match(b, pos):
    """가장 긴 일치, 동점이면 가장 가까운 것. 탐욕적이다 — 최적 파싱은 안 한다.

       O(창 × 최대일치) = 4096 × 18. 20부는 이 단순함의 대가를 실측으로 보인다.
    """
    best_len, best_off = 0, 0
    start = pos - WINDOW
    if start < 0:
        start = 0
    limit = len(b) - pos
    if limit > MAX_MATCH:
        limit = MAX_MATCH
    for j in range(pos - 1, start - 1, -1):        # 가까운 쪽부터 훑는다
        k = 0
        while k < limit and b[j + k] == b[pos + k]:
            k += 1                                 # 겹치는 일치도 허용한다
        if k > best_len:
            best_len, best_off = k, pos - j
            if best_len == limit:
                break
    return best_len, best_off


def lzss_encode(data):
    b = bytearray(data)
    out = bytearray()
    pos = 0
    while pos < len(b):
        flag = 0
        chunk = bytearray()
        bit = 1
        used = 0
        while used < 8 and pos < len(b):
            ln, off = _match(b, pos)
            if ln >= MIN_MATCH:
                o = off - 1                        # 1..4096 → 0..4095
                chunk.append(o // 16)
                chunk.append((o % 16) * 16 + (ln - MIN_MATCH))
                pos += ln
            else:
                flag += bit                        # 비트 1 = 리터럴
                chunk.append(b[pos])
                pos += 1
            bit *= 2
            used += 1
        out.append(flag)
        out += chunk
    return bytes(out)


def lzss_decode(data):
    b = bytearray(data)
    out = bytearray()
    i = 0
    while i < len(b):
        flag = b[i]
        i += 1
        for _k in range(8):
            if i >= len(b):
                break
            if flag % 2 == 1:
                out.append(b[i])
                i += 1
            else:
                o = b[i] * 16 + b[i + 1] // 16
                ln = b[i + 1] % 16 + MIN_MATCH
                i += 2
                src = len(out) - (o + 1)
                for j in range(ln):
                    out.append(out[src + j])       # 한 바이트씩 — 겹침 허용
            flag //= 2
    return bytes(out)
