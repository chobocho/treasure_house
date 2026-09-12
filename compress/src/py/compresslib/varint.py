# -*- coding: utf-8 -*-
"""LEB128 가변 길이 정수 — SPEC §2.1.

명세에서는 intcode 모듈의 일부지만 파일은 따로 뒀다. 모든 코덱의 헤더가
varint 로 시작하는데, intcode 자신은 비트 스트림(bitio)을 쓰고, bitio 의
골든 코덱은 다시 varint 를 쓴다 — 한 파일에 두면 순환 import 가 된다.
다섯 언어 모두 같은 이유로 같은 모양으로 갈라 뒀다.

낮은 7비트부터 내보내고 이어짐 표시는 0x80 이다. 최대 10바이트.
시간·공간 모두 O(값의 비트 수 / 7).
"""

MAX_BYTES = 10
# 길이 칸의 상한. 손상된 헤더가 32비트 기계에 불가능한 할당을 요구하지
# 못하게 막는다 (SPEC §12.1). 코퍼스에서 가장 큰 파일이 1 MiB 다.
MAX_LENGTH = 0xFFFFFFFF


def put(value):
    """정수 하나를 바이트로. value 는 0 이상."""
    if value < 0:
        raise ValueError('varint 는 음수를 못 싣는다: %d' % value)
    out = bytearray()
    while True:
        b = value & 0x7F
        value >>= 7
        if value:
            out.append(b | 0x80)
        else:
            out.append(b)
            return bytes(out)


def get(src, pos=0):
    """(값, 다음 위치). 10바이트를 넘거나 64비트를 넘으면 오류."""
    value = 0
    shift = 0
    for i in range(MAX_BYTES):
        if pos >= len(src):
            raise ValueError('varint 가 잘렸다')
        b = src[pos]
        pos += 1
        value |= (b & 0x7F) << shift
        if not (b & 0x80):
            if value > (1 << 64) - 1:
                raise ValueError('varint 가 64비트를 넘는다')
            return value, pos
        shift += 7
    raise ValueError('varint 가 %d바이트를 넘는다' % MAX_BYTES)


def get_length(src, pos=0):
    """길이 칸을 읽는다 — 상한 검사가 붙은 get()."""
    value, pos = get(src, pos)
    if value > MAX_LENGTH:
        raise ValueError('길이 칸이 너무 크다: %d' % value)
    return value, pos
