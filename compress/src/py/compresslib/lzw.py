# -*- coding: utf-8 -*-
"""LZ78 계열 — SPEC §7.

LZ77 이 "몇 칸 앞을 보라" 고 가리킨다면, LZW 는 **사전을 키워 가며
번호로 부른다.** 사전을 따로 보내지 않는 것이 요점이다 — 복호기가 같은
규칙으로 같은 사전을 다시 짓는다. GIF 와 compress(.Z) 가 이것이다.

폭은 9비트로 시작해 12비트까지 커지고, 사전이 4096 이 되면 CLEAR(256)를
보내고 처음으로 돌아간다. EOF 는 257 이다.

가장 잘 틀리는 자리: **복호기는 부호기보다 항목 하나 뒤처진다.**
부호기가 i번째 부호를 낼 때 사전에는 i-1 개가 있는데, 복호기가 i번째
부호를 읽는 시점에는 i-2 개뿐이다. 그래서 폭을 늘리는 조건이 부호기는
next_free, 복호기는 next_free + 1 이다. 이 한 칸을 틀리면 사전
254번째 항목쯤에서 어긋나기 시작한다 — 작은 시험으로는 절대 안 잡힌다.

시간 O(입력 길이), 공간 O(사전 크기).
"""
from compresslib import bitio, varint

CLEAR = 256
EOF = 257
FIRST_FREE = 258
MIN_WIDTH = 9
MAX_WIDTH = 12
DICT_CAP = 1 << MAX_WIDTH


def encode(src):
    w = bitio.MsbWriter()
    table = {}
    next_free = FIRST_FREE
    width = MIN_WIDTH
    cur = b''
    for k in src:
        if not cur:
            cur = bytes([k])
            continue
        nxt = cur + bytes([k])
        if nxt in table:
            cur = nxt
            continue
        w.write_bits(table[cur] if len(cur) > 1 else cur[0], width)
        if next_free == DICT_CAP:
            # 사전이 꽉 찼다. 4096번째 항목을 만드는 대신 CLEAR 를
            # 보낸다.
            w.write_bits(CLEAR, width)
            table = {}
            next_free = FIRST_FREE
            width = MIN_WIDTH
        else:
            table[nxt] = next_free
            next_free += 1
            # 폭 검사는 항목을 넣은 **뒤에** 한다. 그래서 이 부호가
            # 아니라 다음 부호부터 넓어진다 — 복호기의 한 칸 지연과
            # 맞물린다.
            if next_free == (1 << width) and width < MAX_WIDTH:
                width += 1
        cur = bytes([k])
    if cur:
        w.write_bits(table[cur] if len(cur) > 1 else cur[0], width)
    w.write_bits(EOF, width)
    w.flush()
    return varint.put(len(src)) + w.bytes()


def decode(src):
    n, pos = varint.get_length(src)
    r = bitio.MsbReader(src, pos)
    out = bytearray()
    table = {}
    next_free = FIRST_FREE
    width = MIN_WIDTH
    prev = None
    while True:
        code = r.read_bits(width)
        if code == EOF:
            break
        if code == CLEAR:
            table = {}
            next_free = FIRST_FREE
            width = MIN_WIDTH
            prev = None
            continue
        if prev is None:
            if code >= CLEAR:
                raise ValueError('첫 부호가 리터럴이 아니다: %d' % code)
            entry = bytes([code])
        elif code < 256:
            entry = bytes([code])
        elif code < next_free:
            entry = table[code]
        elif code == next_free:
            # KwKwK — 부호기가 방금 만든 항목이다. 언제나 prev + prev[0]
            # 이다.
            entry = prev + prev[:1]
        else:
            raise ValueError('아직 없는 부호: %d' % code)
        out += entry
        if len(out) > n:
            raise ValueError('푼 길이가 헤더를 넘었다')
        if prev is not None:
            table[next_free] = prev + entry[:1]
            next_free += 1
            # 복호기는 한 칸 뒤처져 있다. + 1 이 그 보정이다.
            if next_free + 1 == (1 << width) and width < MAX_WIDTH:
                width += 1
        prev = entry
    if len(out) != n:
        raise ValueError('푼 길이가 헤더와 다르다: %d != %d'
                         % (len(out), n))
    return bytes(out)
