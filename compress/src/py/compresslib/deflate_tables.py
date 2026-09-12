# -*- coding: utf-8 -*-
"""DEFLATE 의 표들 — SPEC §10.3 (RFC 1951 §3.2.5, §3.2.6, §3.2.7).

숫자를 소스에 적어 두지 않고 짧은 원본 배열에서 **만든다.** 길이 부호
스물아홉 개와 거리 부호 서른 개를 다섯 언어에 손으로 옮기면 어딘가는
틀리고, 그 자리는 그 부호를 쓰는 입력을 만나기 전까지 안 보인다.

길이 부호 284 는 227..257 까지만 적을 수 있고, **길이 258 은 늘 285**
다. 284 + 여분 31 로도 258 이 되지만 진짜 부호기는 아무도 그러지 않는다.
"""

# (여분 비트 수, 시작 길이) — 부호 257..285
LENGTH_SPEC = [
    (0, 3), (0, 4), (0, 5), (0, 6), (0, 7), (0, 8), (0, 9), (0, 10),
    (1, 11), (1, 13), (1, 15), (1, 17),
    (2, 19), (2, 23), (2, 27), (2, 31),
    (3, 35), (3, 43), (3, 51), (3, 59),
    (4, 67), (4, 83), (4, 99), (4, 115),
    (5, 131), (5, 163), (5, 195), (5, 227),
    (0, 258),
]
# (여분 비트 수, 시작 거리) — 부호 0..29
DIST_SPEC = [
    (0, 1), (0, 2), (0, 3), (0, 4), (1, 5), (1, 7), (2, 9), (2, 13),
    (3, 17), (3, 25), (4, 33), (4, 49), (5, 65), (5, 97),
    (6, 129), (6, 193), (7, 257), (7, 385), (8, 513), (8, 769),
    (9, 1025), (9, 1537), (10, 2049), (10, 3073),
    (11, 4097), (11, 6145),
    (12, 8193), (12, 12289), (13, 16385), (13, 24577),
]

LENGTH_EXTRA = [e for e, _b in LENGTH_SPEC]
LENGTH_BASE = [b for _e, b in LENGTH_SPEC]
DIST_EXTRA = [e for e, _b in DIST_SPEC]
DIST_BASE = [b for _e, b in DIST_SPEC]

MIN_MATCH = 3
MAX_MATCH = 258
MAX_DIST = 32768
END_OF_BLOCK = 256
LITLEN_SYMBOLS = 286
DIST_SYMBOLS = 30

# 부호 길이 알파벳을 보내는 순서. 자주 0 이 되는 것을 뒤로 몰아 두어
# HCLEN 으로 꼬리를 잘라 낼 수 있게 한 배열이다 (RFC 1951 §3.2.7).
CL_ORDER = [16, 17, 18, 0, 8, 7, 9, 6, 10,
            5, 11, 4, 12, 3, 13, 2, 14, 1, 15]
CL_SYMBOLS = 19
CL_MAX_LENGTH = 7
CL_REPEAT = 16          # 앞 길이를 3..6번 (여분 2비트)
CL_ZERO_SHORT = 17      # 0 을 3..10번 (여분 3비트)
CL_ZERO_LONG = 18       # 0 을 11..138번 (여분 7비트)


def _length_code_table():
    """길이 3..258 → 부호(257..285). 미리 펼쳐 두면 찾기가 O(1)."""
    table = [0] * (MAX_MATCH + 1)
    for code, (extra, base) in enumerate(LENGTH_SPEC):
        top = base + (1 << extra) - 1
        if base == MAX_MATCH:               # 285 — 258 하나뿐
            top = MAX_MATCH
        for ln in range(base, min(top, MAX_MATCH) + 1):
            table[ln] = 257 + code
    table[MAX_MATCH] = 285          # 284 가 아니라 285 로 못 박는다
    return table


LENGTH_CODE = _length_code_table()


def dist_code(dist):
    """거리 1..32768 → 부호 0..29. 서른 개뿐이라 선형으로 찾는다."""
    for code in range(DIST_SYMBOLS - 1, -1, -1):
        if dist >= DIST_BASE[code]:
            return code
    raise ValueError('거리가 1보다 작다: %d' % dist)


def fixed_litlen_lengths():
    """고정 블록의 리터럴·길이 부호 길이 288칸 (RFC 1951 §3.2.6)."""
    lengths = [8] * 288
    for s in range(144, 256):
        lengths[s] = 9
    for s in range(256, 280):
        lengths[s] = 7
    return lengths


def fixed_dist_lengths():
    return [5] * 32


FIXED_LITLEN = fixed_litlen_lengths()
FIXED_DIST = fixed_dist_lengths()
