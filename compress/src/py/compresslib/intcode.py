# -*- coding: utf-8 -*-
"""정수 부호 — SPEC §2.

값 하나를 비트 몇 개로 적을 것인가. 고정 길이(32비트)는 작은 값에서
낭비고, 가변 길이는 "어디서 끝나는가" 를 스스로 말해야 한다. 그 말하는
방식이 부호마다 다르고, 그 차이가 곧 이 파일이다.

  varint  바이트 단위. 이어짐 표시 한 비트 — 헤더에 쓴다
  zigzag  음수를 작은 양수로 접는다
  gamma   길이를 단항으로 먼저 — 작은 값에 최적
  delta   길이를 다시 gamma 로 — 큰 값에서 gamma 를 이긴다
  rice(k) 몫은 단항, 나머지는 k비트 — 기하분포에 맞춘다

varint 만 바이트 단위이고 나머지 넷은 비트 스트림(bitio)에서 돈다.
varint 의 실제 구현은 varint.py 다 — 순환 import 를 피하려 갈랐다.
값 하나당 O(비트 수).
"""
from compresslib import varint

put_varint = varint.put

# 아래 셋은 varint.py 의 것을 그대로 쓴다. 명세(§2.1)상 한 모듈이므로
# 이름만 여기로 끌어와, 쓰는 쪽이 varint.py 를 몰라도 되게 한다.
MAX_VARINT_BYTES = varint.MAX_BYTES


def get_varint(src, pos=0):
    return varint.get(src, pos)


MASK64 = (1 << 64) - 1
# 단항 부분의 상한 (SPEC §2.5). 상한이 없으면 손상된 파일이 무한 루프가
# 되고, 너무 작으면 부호 자체가 쓸모없어진다 — k=0 인 rice 가 곧
# 단항이라 상한 64 는 100 도 못 적는다. 4096 이면 손상 시 4 Ki 번으로
# 끝난다.
MAX_UNARY = 4096


def zigzag(n):
    """음수를 작은 양수로. -1→1, 1→2, -2→3 …"""
    if not -(1 << 63) <= n <= (1 << 63) - 1:
        raise ValueError('zigzag 는 64비트 부호 있는 정수만: %d' % n)
    return ((n << 1) ^ (n >> 63)) & MASK64


def unzigzag(u):
    """zigzag 의 역. >> 는 여기서 논리 시프트다."""
    return (u >> 1) ^ -(u & 1)


def bit_length(v):
    """v 의 비트 수. bit_length(1) = 1. 0 은 정의하지 않는다."""
    return v.bit_length()


def put_gamma(w, v):
    """엘리아스 감마. 0 은 못 싣는다 — 0 이 필요하면 v+1 을 실어라."""
    if v < 1:
        raise ValueError('gamma 는 1 이상만: %d' % v)
    n = bit_length(v)
    w.write_bits(0, n - 1)
    w.write_bits(v, n)


def get_gamma(r):
    n = 1
    while r.read_bit() == 0:
        n += 1
        if n > 64:
            raise ValueError('gamma 의 길이 부분이 64비트를 넘는다')
    # 방금 읽은 1 이 값의 맨 위 비트다
    return (1 << (n - 1)) | r.read_bits(n - 1)


def put_delta(w, v):
    """엘리아스 델타. 길이를 감마로, 값은 맨 위 1 을 빼고 적는다."""
    if v < 1:
        raise ValueError('delta 는 1 이상만: %d' % v)
    n = bit_length(v)
    put_gamma(w, n)
    w.write_bits(v, n - 1)


def get_delta(r):
    n = get_gamma(r)
    if n > 64:
        raise ValueError('delta 의 길이 부분이 64비트를 넘는다')
    return (1 << (n - 1)) | r.read_bits(n - 1)


def put_rice(w, v, k):
    """골룸–라이스. 단항은 **1 을 q개 쓰고 0 으로 닫는다.**

    반대 약속(0 을 q개 쓰고 1 로 닫기)도 문헌에 흔하다. 섞어 쓰면
    작은 값은 그래도 왕복이 되어, 골든 벡터를 맞출 때까지 안 보인다.
    """
    if v < 0:
        raise ValueError('rice 는 0 이상만: %d' % v)
    q = v >> k
    if q > MAX_UNARY:
        raise ValueError('rice 의 몫이 %d — k 를 잘못 골랐다' % q)
    w.write_bits((1 << q) - 1, q)
    w.write_bit(0)
    if k:
        w.write_bits(v & ((1 << k) - 1), k)


def get_rice(r, k):
    q = 0
    while r.read_bit() == 1:
        q += 1
        if q > MAX_UNARY:
            raise ValueError('rice 의 단항이 %d 를 넘는다' % MAX_UNARY)
    return (q << k) | (r.read_bits(k) if k else 0)


# ------------------------------------------------------------ 골든 코덱
# SPEC §2.6. 바이트마다 gamma(b+1). 0 바이트는 비트 하나가 되고 0xff 는
# 17비트가 된다 — 낮은 값이 많은 파일만 줄어든다. 이게 "부호를 값의
# 분포에 맞춘다" 는 말의 가장 작은 예다.
from compresslib import bitio                      # noqa: E402


def encode(src):
    w = bitio.MsbWriter()
    for b in src:
        put_gamma(w, b + 1)
    w.flush()
    return varint.put(len(src)) + w.bytes()


def decode(src):
    n, pos = varint.get_length(src)
    r = bitio.MsbReader(src, pos)
    out = bytearray()
    for _ in range(n):
        v = get_gamma(r) - 1
        if not 0 <= v <= 255:
            raise ValueError('바이트 범위를 벗어난 값: %d' % v)
        out.append(v)
    return bytes(out)
