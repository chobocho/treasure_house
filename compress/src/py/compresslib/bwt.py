# -*- coding: utf-8 -*-
"""버로스–휠러 변환 — SPEC §9.

블록의 회전을 전부 사전순으로 세우고 **마지막 글자만** 모은다.
그것뿐인데 결과는 같은 글자가 몰린 열이 된다. 앞 글자가 같으면 뒤도
비슷하기 때문이다 — 영어에서 "he" 앞에는 거의 늘 t 가 온다.

한 바이트도 줄지 않는다. 길이가 같은 **치환** 이기 때문이다. 줄이는 일은
뒤에 붙는 MTF·0런·허프만이 한다. 그 조립이 bzip2 다(10부).

정렬은 배가 늘리기(suffix doubling)다. O(m log^2 m) 시간, O(m) 공간.
같은 회전이 여럿이면(zeros_64k 는 전부 같다) 배가 늘리기로는 영영 안
갈린다 — 그때의 순서는 **시작 위치 오름차순** 이다. 파이썬의 sort 가
안정 정렬이라 저절로 그렇게 되지만, 안정이 아닌 정렬을 쓰는 언어에서는
같은 결과가 안 나온다. 그래서 명세에 못 박혀 있다.

되돌리기는 LF 매핑이다. 여기서는 뒤에서부터가 아니라 **앞에서부터** 내는
꼴을 쓴다 — 다 만든 뒤 64 KiB 를 한 번 더 뒤집는 할당을 C++·Go 에서
피하려는 것이다. 둘 다 맞지만 골든 벡터는 하나여야 하므로 고정했다.
"""
from compresslib import varint

BLOCK = 1 << 16          # 64 KiB. bzip2 의 900 KiB 는 13번 모듈에서.
ALPHABET = 256


def transform_block(block):
    """(L 열, primary). 블록 하나짜리 BWT."""
    m = len(block)
    if m == 0:
        return b'', 0
    # 바이트 값을 0..(서로 다른 값의 수 - 1) 로 먼저 압축한다. 이걸 빼면
    # 아래 키 packing 의 곱수 m+1 이 바이트 값(최대 255)보다 작아져
    # 순서가 통째로 망가진다 — banana 에서 'ba' 가 'an' 앞에 서는
    # 식이다.
    order = {c: i for i, c in enumerate(sorted(set(block)))}
    rank = [order[c] for c in block]
    sa = list(range(m))
    k = 1
    while True:
        # 키를 정수 하나로 눌러 담는다. 튜플로 두면 비교마다 객체가 생겨
        # 64 KiB 블록에서 눈에 띄게 느려진다 — 다른 언어도 같게 한다.
        # 순위가 늘 m 미만이므로 곱수 m+1 이면 자리가 겹치지 않는다.
        keys = [rank[i] * (m + 1) + rank[(i + k) % m] for i in range(m)]
        sa.sort(key=keys.__getitem__)
        new_rank = [0] * m
        r = 0
        for j in range(1, m):
            if keys[sa[j]] != keys[sa[j - 1]]:
                r += 1
            new_rank[sa[j]] = r
        rank = new_rank
        if r == m - 1 or k >= m:
            break
        k *= 2
    L = bytes(block[(i - 1) % m] for i in sa)
    return L, sa.index(0)


def inverse_block(L, primary):
    """LF 매핑으로 되돌린다. O(m + 256) 시간."""
    m = len(L)
    if m == 0:
        return b''
    if not 0 <= primary < m:
        raise ValueError('primary 가 범위 밖이다: %d' % primary)
    count = [0] * ALPHABET
    for c in L:
        count[c] += 1
    first = [0] * ALPHABET
    total = 0
    for c in range(ALPHABET):
        first[c] = total
        total += count[c]
    lf = [0] * m
    occ = [0] * ALPHABET
    for i, c in enumerate(L):
        lf[i] = first[c] + occ[c]
        occ[c] += 1
    # T 는 LF 의 역치환이다. LF 로 걸으면 원문이 거꾸로 나오고,
    # T 로 걸으면 바로 나온다.
    nxt = [0] * m
    for i in range(m):
        nxt[lf[i]] = i
    out = bytearray()
    i = primary
    for _ in range(m):
        i = nxt[i]
        out.append(L[i])
    return bytes(out)


def encode(src):
    out = bytearray(varint.put(len(src)))
    for off in range(0, len(src), BLOCK):
        L, primary = transform_block(src[off:off + BLOCK])
        out += primary.to_bytes(4, 'little')
        out += L
    return bytes(out)


def decode(src):
    n, pos = varint.get_length(src)
    out = bytearray()
    left = n
    while left > 0:
        m = min(BLOCK, left)
        if pos + 4 + m > len(src):
            raise ValueError('블록이 잘렸다')
        primary = int.from_bytes(src[pos:pos + 4], 'little')
        pos += 4
        out += inverse_block(src[pos:pos + m], primary)
        pos += m
        left -= m
    if pos != len(src):
        raise ValueError('뒤에 남은 바이트가 있다')
    return bytes(out)
