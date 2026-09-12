# -*- coding: utf-8 -*-
"""런 길이 부호 — SPEC §3.

같은 바이트가 이어지면 "그 바이트와 개수" 로 적는다. 가장 단순한
압축이고, 그래서 한계도 가장 먼저 보인다 — 런이 없으면 반드시 커진다.

여기 둘이 있다.
  PackBits  바이트 단위. 리터럴 묶음과 런 묶음을 제어 바이트로 가른다
  0런 부호  MTF 뒤의 0 무더기를 위한 것. bzip2 가 쓰는 RUNA/RUNB 다

PackBits 에서 정한 것 셋: 문턱 3, 런 상한 128, 리터럴 상한 128.
셋 다 출력 바이트를 바꾸는 결정이라 SPEC §3.1 에 못 박혀 있다.
시간·공간 모두 O(입력 길이).
"""
from compresslib import varint

RUN_MIN = 3
RUN_MAX = 128
LIT_MAX = 128
# 제어 128 은 안 쓴다. 애플 원본은 "아무 일도 안 함" 으로 넘어가지만,
# 같은 입력을 두 가지 바이트로 적을 수 있는 부호기는 골든 벡터를 못
# 가진다.
RESERVED = 128


def _run_at(src, i, cap=RUN_MAX):
    """i 에서 시작하는 같은 바이트의 길이 (cap 까지)."""
    b = src[i]
    j = i + 1
    end = min(len(src), i + cap)
    while j < end and src[j] == b:
        j += 1
    return j - i


def pack(src):
    """PackBits 묶음들. 헤더는 붙이지 않는다."""
    out = bytearray()
    i, n = 0, len(src)
    while i < n:
        run = _run_at(src, i)
        if run >= RUN_MIN:
            out.append(257 - run)
            out.append(src[i])
            i += run
            continue
        # 리터럴 — 런이 시작되는 자리까지, 또는 상한까지
        j = i
        while j < n and (j - i) < LIT_MAX:
            r = _run_at(src, j)
            if r >= RUN_MIN:
                break
            # 상한을 넘겨 잡으면 129바이트 묶음이 나온다. 제어 바이트에
            # 안 들어가는 길이라, 아무도 못 푸는 파일이 된다.
            j = min(j + r, i + LIT_MAX)
        out.append(j - i - 1)
        out += src[i:j]
        i = j
    return bytes(out)


def unpack(src, pos, want):
    """묶음을 풀어 want 바이트를 만든다. (바이트, 다음 위치)."""
    out = bytearray()
    n = len(src)
    while len(out) < want:
        if pos >= n:
            raise ValueError('PackBits 가 잘렸다')
        c = src[pos]
        pos += 1
        if c == RESERVED:
            raise ValueError('제어 128 은 쓰지 않는다')
        if c < RESERVED:
            k = c + 1
            if pos + k > n:
                raise ValueError('리터럴 묶음이 잘렸다')
            out += src[pos:pos + k]
            pos += k
        else:
            k = 257 - c
            if pos >= n:
                raise ValueError('런 묶음이 잘렸다')
            out += bytes([src[pos]]) * k
            pos += 1
    if len(out) != want:
        raise ValueError('푼 길이가 헤더와 다르다: %d != %d'
                         % (len(out), want))
    return bytes(out), pos


def encode(src):
    return varint.put(len(src)) + pack(src)


def decode(src):
    n, pos = varint.get_length(src)
    out, pos = unpack(src, pos, n)
    if pos != len(src):
        raise ValueError('뒤에 남은 바이트가 있다')
    return out


# ---------------------------------------------------------------- 0런
# 부호 SPEC §3.2. MTF 를 거친 열은 0 이 압도적으로 많다. 그 0 무더기를
# 이진법의 **자릿수** 로 적는다 — RUNA 가 1, RUNB 가 2 를 나타내는 쌍대
# 이진법이라 앞자리 0 이 없고, 그래서 같은 길이를 두 가지로 적을 수
# 없다.
RUNA = 0
RUNB = 1


def zero_run_encode(symbols):
    """MTF 기호 열 → 0런이 접힌 열. 0 아닌 기호는 한 칸씩 밀린다."""
    out = []
    i, n = 0, len(symbols)
    while i < n:
        if symbols[i] != 0:
            out.append(symbols[i] + 1)
            i += 1
            continue
        j = i
        while j < n and symbols[j] == 0:
            j += 1
        length = (j - i) + 1
        while length > 1:
            out.append(RUNB if (length & 1) else RUNA)
            length >>= 1
        i = j
    return out


def zero_run_decode(symbols):
    out = []
    i, n = 0, len(symbols)
    while i < n:
        if symbols[i] > 1:
            out.append(symbols[i] - 1)
            i += 1
            continue
        run, weight = 0, 1
        while i < n and symbols[i] <= 1:
            run += (symbols[i] + 1) * weight
            weight <<= 1
            i += 1
        out += [0] * run
    return out
