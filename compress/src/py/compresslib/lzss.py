# -*- coding: utf-8 -*-
"""LZ77 계열 — SPEC §6.

사전을 따로 두지 않는다. **이미 내보낸 문서 자신이 사전** 이고,
되풀이되는 토막은 "몇 칸 앞의 몇 바이트" 라는 두 숫자로 가리킨다.
gzip·zstd·lz4 가 전부 이 한 줄의 변주다.

정한 값들(§6.1)은 전부 출력 바이트를 바꾼다:
  창 32768 · 최소 3 · 최대 258 · 사슬 32번 · 같은 길이면 가까운 쪽

사슬 배열을 **절대 위치로** 잡는 것이 zlib 과 다르다. zlib 은 창 크기
배열에 감아 넣어서, pos - 32768 자리는 이미 pos 가 덮어썼다 — 그래서
zlib 의 실효 최대 거리는 32506 이다. 우리는 메모리를 O(n) 쓰는 대신
32768 을 진짜로 닿는다. corpus/boundary_32768.bin 이 그걸 본다.

찾기는 위치마다 최대 32번 × 최대 258바이트 비교라 O(n)에 상수가 붙는다.
"""
from compresslib import varint

WINDOW = 32768
MIN_MATCH = 3
MAX_MATCH = 258
HASH_BITS = 15
HASH_SIZE = 1 << HASH_BITS
CHAIN_LIMIT = 32
NIL = -1


def _hash3(src, i):
    """3바이트 해시. 자리를 고르는 용도라 충돌해도 괜찮다."""
    h = (src[i] << 10) ^ (src[i + 1] << 5) ^ src[i + 2]
    return h & (HASH_SIZE - 1)


def _match_len(src, a, b, limit):
    """src[a:] 와 src[b:] 가 몇 바이트 같은가 (limit 까지)."""
    n = 0
    while n < limit and src[a + n] == src[b + n]:
        n += 1
    return n


def find_tokens(src):
    """(리터럴 또는 (길이, 거리)) 목록. 부호화의 전부가 여기에 있다."""
    n = len(src)
    head = [NIL] * HASH_SIZE
    prev = [NIL] * max(n, 1)
    tokens = []
    i = 0
    while i < n:
        best_len, best_dist = 0, 0
        if i + MIN_MATCH <= n:
            h = _hash3(src, i)
            cand = head[h]
            limit = min(MAX_MATCH, n - i)
            probes = 0
            while cand != NIL and probes < CHAIN_LIMIT:
                dist = i - cand
                if dist > WINDOW:
                    break
                # 더 길 때만 바꾼다. >= 로 쓰면 같은 길이에서 먼 쪽을
                # 고르게 되고, 정상 복호되는 다른 파일이 나온다.
                ln = _match_len(src, cand, i, limit)
                if ln > best_len:
                    best_len, best_dist = ln, dist
                    if ln == limit:
                        break
                cand = prev[cand]
                probes += 1
        if best_len >= MIN_MATCH:
            # 일치로 덮이는 자리도 전부 해시에 넣는다 — 안 넣으면 뒤에서
            # 그 자리를 시작점으로 하는 일치를 못 찾는다.
            for k in range(best_len):
                p = i + k
                if p + MIN_MATCH <= n:
                    h = _hash3(src, p)
                    prev[p] = head[h]
                    head[h] = p
            tokens.append((best_len, best_dist))
            i += best_len
        else:
            if i + MIN_MATCH <= n:
                h = _hash3(src, i)
                prev[i] = head[h]
                head[h] = i
            tokens.append(src[i])
            i += 1
    return tokens


def pack_tokens(tokens):
    """여덟 개씩 묶어 플래그 바이트를 앞에 붙인다."""
    out = bytearray()
    for base in range(0, len(tokens), 8):
        group = tokens[base:base + 8]
        flag = 0
        for k, t in enumerate(group):
            if isinstance(t, tuple):
                flag |= 1 << (7 - k)
        out.append(flag)
        for t in group:
            if isinstance(t, tuple):
                ln, dist = t
                out.append(ln - MIN_MATCH)
                out.append((dist - 1) & 0xFF)
                out.append((dist - 1) >> 8)
            else:
                out.append(t)
    return bytes(out)


def encode(src):
    return varint.put(len(src)) + pack_tokens(find_tokens(src))


def decode(src):
    n, pos = varint.get_length(src)
    end = len(src)
    out = bytearray()
    while len(out) < n:
        if pos >= end:
            raise ValueError('플래그 바이트가 없다')
        flag = src[pos]
        pos += 1
        for k in range(8):
            if len(out) >= n:
                break
            if flag & (1 << (7 - k)):
                if pos + 3 > end:
                    raise ValueError('일치 토큰이 잘렸다')
                ln = src[pos] + MIN_MATCH
                dist = (src[pos + 1] | (src[pos + 2] << 8)) + 1
                pos += 3
                if dist > len(out):
                    raise ValueError('거리 %d 가 낸 것보다 멀다' % dist)
                start = len(out) - dist
                # 한 바이트씩 앞으로 복사한다. 거리 1 짜리 긴 일치는
                # 자기가 방금 쓴 바이트를 다시 읽어야 하므로 memmove 는
                # 틀린다.
                for j in range(ln):
                    out.append(out[start + j])
            else:
                if pos >= end:
                    raise ValueError('리터럴이 잘렸다')
                out.append(src[pos])
                pos += 1
    if len(out) != n:
        raise ValueError('푼 길이가 헤더와 다르다')
    if pos != end:
        raise ValueError('뒤에 남은 바이트가 있다')
    return bytes(out)
