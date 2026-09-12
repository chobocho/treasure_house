# -*- coding: utf-8 -*-
"""ANS — 비대칭 수 체계 — SPEC §13.

산술 부호화(§8)는 엔트로피 한계에 닿지만 안쪽 고리에 곱셈·나눗셈·캐리가
다 들어 있다. ANS 는 같은 한계에 닿으면서 상태가 **정수 하나** 이고
캐리가 아예 없다. zstd·LZFSE·JPEG-XL 이 전부 이걸 쓰고, 아무도 새 산술
부호기를 안 만드는 이유다.

골든 코덱은 rANS(구간 변형)다. tANS(표 변형 — FSE 가 바로 이것)는
표 만들기만 따로 두고 12부에서 zstd 를 설명할 때 쓴다.

rANS 는 **스택** 이다. 부호기가 입력을 뒤에서부터 밀어 넣고 복호기가
앞에서부터 꺼낸다. 이 방향이 헷갈리면 왕복은 되는데 바이트가 달라진다.

시간은 기호당 O(1), 공간은 표 4096칸.
"""
from compresslib import varint

TOTAL_BITS = 12
TOTAL = 1 << TOTAL_BITS          # 빈도의 합은 정확히 이 값이다
L = 1 << 23                      # 상태의 하한. 상태는 [L, L*256) 이다
ALPHABET = 256
# tANS 의 퍼뜨리기 걸음 (zstd 의 값). 홀수라서 2의 거듭제곱 칸을
# 빠짐없이 한 번씩 돈다 — 상수가 이상해 보이는 이유가 그것 하나다.
SPREAD_STEP = (TOTAL >> 1) + (TOTAL >> 3) + 3


def normalise(counts):
    """세어 온 빈도를 합이 정확히 TOTAL 이 되게 고친다 (SPEC §13.3).

    나머지를 어디에 붙이느냐가 언어마다 갈리는 자리다. 남으면 가장 큰
    기호에 한꺼번에, 모자라면 가장 큰 기호에서 되풀이해 뺀다.
    동점이면 번호가 작은 쪽. 그 규칙이 전부다.
    """
    total = sum(counts)
    if total == 0:
        return [0] * ALPHABET
    f = [0] * ALPHABET
    for s in range(ALPHABET):
        if counts[s]:
            f[s] = max(1, counts[s] * TOTAL // total)
    d = TOTAL - sum(f)
    while d:
        # 가장 큰 빈도, 동점이면 작은 번호
        s = max(range(ALPHABET), key=lambda i: (f[i], -i))
        if d > 0:
            f[s] += d
            d = 0
        else:
            take = min(-d, f[s] - 1)
            if take == 0:
                raise ValueError('빈도를 TOTAL 에 못 맞춘다')
            f[s] -= take
            d += take
    return f


def cumulative(f):
    """배타적 누적합. cum[s] 는 기호 s 의 칸이 시작하는 자리다."""
    cum = [0] * ALPHABET
    total = 0
    for s in range(ALPHABET):
        cum[s] = total
        total += f[s]
    return cum


def slot_symbols(f, cum):
    """칸 번호 → 기호. 복호기가 상태의 아래 12비트로 바로 찾는다."""
    slots = [0] * TOTAL
    for s in range(ALPHABET):
        for i in range(cum[s], cum[s] + f[s]):
            slots[i] = s
    return slots


def tans_table(f):
    """tANS 의 상태표를 퍼뜨려 만든다 (SPEC §13.6). 골든에는 없다."""
    table = [0] * TOTAL
    pos = 0
    for s in range(ALPHABET):
        for _ in range(f[s]):
            table[pos] = s
            pos = (pos + SPREAD_STEP) & (TOTAL - 1)
    return table


def encode(src):
    if not src:
        return varint.put(0)
    counts = [0] * ALPHABET
    for b in src:
        counts[b] += 1
    f = normalise(counts)
    cum = cumulative(f)

    out = bytearray()
    x = L
    # 뒤에서부터 민다. rANS 는 스택이고, 마지막에 넣은 것이 먼저 나온다.
    for b in reversed(src):
        fs = f[b]
        x_max = ((L >> TOTAL_BITS) << 8) * fs
        while x >= x_max:
            out.append(x & 0xFF)
            x >>= 8
        x = (x // fs) * TOTAL + (x % fs) + cum[b]
    for i in range(4):
        out.append((x >> (8 * i)) & 0xFF)
    out.reverse()

    head = bytearray(varint.put(len(src)))
    for s in range(ALPHABET):
        head += varint.put(f[s])
    return bytes(head + out)


def decode(src):
    n, pos = varint.get_length(src)
    if n == 0:
        if pos != len(src):
            raise ValueError('빈 입력인데 뒤에 바이트가 있다')
        return b''
    f = [0] * ALPHABET
    for s in range(ALPHABET):
        v, pos = varint.get(src, pos)
        if v > TOTAL:
            raise ValueError('빈도가 TOTAL 을 넘는다')
        f[s] = v
    if sum(f) != TOTAL:
        raise ValueError('빈도의 합이 %d 가 아니다' % TOTAL)
    cum = cumulative(f)
    slots = slot_symbols(f, cum)

    body = src[pos:]
    if len(body) < 4:
        raise ValueError('rANS 스트림이 너무 짧다')
    x = 0
    for i in range(4):
        x = (x << 8) | body[i]
    at = 4
    out = bytearray()
    mask = TOTAL - 1
    for _ in range(n):
        slot = x & mask
        s = slots[slot]
        out.append(s)
        x = f[s] * (x >> TOTAL_BITS) + slot - cum[s]
        while x < L:
            if at >= len(body):
                raise ValueError('rANS 스트림이 모자란다')
            x = (x << 8) | body[at]
            at += 1
    if at != len(body):
        raise ValueError('뒤에 남은 바이트가 있다')
    return bytes(out)
