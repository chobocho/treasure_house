# -*- coding: utf-8 -*-
"""DEFLATE 부호기 — SPEC §10.

RFC 1951 이 부호기에 맡긴 선택을 전부 못 박은 것이 이 파일이다. 형식은
남의 것이지만 **어떤 파일을 낼지** 는 우리가 정한다. 그 선택이 정해져
있어야 다섯 언어가 같은 바이트를 낸다.

정한 것:
  · 블록 65535 바이트 (stored 의 LEN 이 16비트라 65536 은 못 담는다)
  · 세 종류의 값을 정확히 세어 가장 작은 것. 같으면 stored→fixed→dynamic
  · 일치 찾기는 해시 사슬 128번 + 게으른 일치 (§10.4)
  · gzip 헤더의 MTIME 은 0 — 진짜 gzip 과 달리 우리 출력은 재현된다

zlib 에 있는 good_match·nice_length 같은 조절기는 안 둔다. 그것들이 zlib
출력을 압축 수준에 따라 달라지게 하는 물건이고, 우리는 한 가지 행동만
한다. 진짜 gzip -9 와의 비율 차이는 9부에서 캡처로 견준다.

찾기는 위치마다 최대 128번 × 최대 258바이트 비교다.
"""
from compresslib import bitio, huffman, inflate
from compresslib import deflate_tables as T

BLOCK_SIZE = 65535
HASH_BITS = 15
HASH_SIZE = 1 << HASH_BITS
CHAIN_LIMIT = 128
NIL = -1

STORED, FIXED, DYNAMIC = 0, 1, 2


# -------------------------------------------------------------------
# 파싱
def _hash3(src, i):
    h = (src[i] << 10) ^ (src[i + 1] << 5) ^ src[i + 2]
    return h & (HASH_SIZE - 1)


def parse(src):
    """리터럴과 (길이, 거리) 의 열. 게으른 일치까지 여기서 끝낸다."""
    n = len(src)
    head = [NIL] * HASH_SIZE
    prev = [NIL] * max(n, 1)
    tokens = []

    def insert(p):
        if p + T.MIN_MATCH <= n:
            h = _hash3(src, p)
            prev[p] = head[h]
            head[h] = p

    def find(p):
        if p + T.MIN_MATCH > n:
            return 0, 0
        best_len = best_dist = 0
        limit = min(T.MAX_MATCH, n - p)
        cand = head[_hash3(src, p)]
        probes = 0
        while cand != NIL and probes < CHAIN_LIMIT:
            dist = p - cand
            if dist > T.MAX_DIST:
                break
            ln = 0
            while ln < limit and src[cand + ln] == src[p + ln]:
                ln += 1
            if ln > best_len:
                best_len, best_dist = ln, dist
                if ln == limit:
                    break
            cand = prev[cand]
            probes += 1
        return best_len, best_dist

    i = 0
    while i < n:
        ln, dist = find(i)
        insert(i)
        if ln >= T.MIN_MATCH:
            # 게으른 일치 — 한 칸 뒤에서 **더 긴** 것이 있으면 이번은
            # 버린다.
            nxt_len = find(i + 1)[0] if i + 1 < n else 0
            if nxt_len > ln:
                tokens.append(src[i])
                i += 1
                continue
            for k in range(1, ln):
                insert(i + k)
            tokens.append((ln, dist))
            i += ln
        else:
            tokens.append(src[i])
            i += 1
    return tokens


def split_blocks(tokens):
    """(토큰 시작, 토큰 끝, 입력 시작, 입력 끝) 목록."""
    blocks = []
    tok_start, in_start, cur = 0, 0, 0
    for k, t in enumerate(tokens):
        cur += t[0] if isinstance(t, tuple) else 1
        if cur >= BLOCK_SIZE:
            blocks.append((tok_start, k + 1, in_start, in_start + cur))
            tok_start, in_start, cur = k + 1, in_start + cur, 0
    if cur or not blocks:
        blocks.append((tok_start, len(tokens),
                       in_start, in_start + cur))
    return blocks


# ------------------------------------------------------------- 값 계산
def _freqs(tokens):
    lit = [0] * T.LITLEN_SYMBOLS
    dst = [0] * T.DIST_SYMBOLS
    extra = 0
    for t in tokens:
        if isinstance(t, tuple):
            ln, d = t
            code = T.LENGTH_CODE[ln]
            lit[code] += 1
            extra += T.LENGTH_EXTRA[code - 257]
            dc = T.dist_code(d)
            dst[dc] += 1
            extra += T.DIST_EXTRA[dc]
        else:
            lit[t] += 1
    lit[T.END_OF_BLOCK] += 1
    return lit, dst, extra


def _body_bits(lit_freq, dst_freq, extra, lit_len, dst_len):
    bits = extra
    for s, f in enumerate(lit_freq):
        if f:
            bits += f * lit_len[s]
    for s, f in enumerate(dst_freq):
        if f:
            bits += f * dst_len[s]
    return bits


def cl_encode(lengths):
    """부호 길이 배열 → (기호, 여분 값, 여분 비트). 왼쪽부터 탐욕."""
    out = []
    i, n = 0, len(lengths)
    while i < n:
        cur = lengths[i]
        run = 1
        while i + run < n and lengths[i + run] == cur:
            run += 1
        if cur == 0:
            while run >= 3:
                if run >= 11:
                    k = min(run, 138)
                    out.append((T.CL_ZERO_LONG, k - 11, 7))
                else:
                    k = min(run, 10)
                    out.append((T.CL_ZERO_SHORT, k - 3, 3))
                run -= k
                i += k
            for _ in range(run):
                out.append((0, 0, 0))
                i += 1
        else:
            out.append((cur, 0, 0))
            i += 1
            run -= 1
            while run >= 3:
                k = min(run, 6)
                out.append((T.CL_REPEAT, k - 3, 2))
                run -= k
                i += k
            for _ in range(run):
                out.append((cur, 0, 0))
                i += 1
    return out


class DynamicPlan:
    """동적 블록 하나를 쓰는 데 필요한 것 전부와 그 비트 수."""

    def __init__(self, lit_freq, dst_freq, extra):
        lim = huffman.MAX_LENGTH
        self.lit_len = huffman.code_lengths(lit_freq, lim)
        self.dst_len = huffman.code_lengths(dst_freq, lim)
        if not any(self.dst_len):
            # 일치가 하나도 없는 블록. 거리 부호를 안 보낼 수는 없으므로
            # 하나를 길이 1 로 보낸다 — 쓰이지 않는 부호다 (§10.5).
            self.dst_len[0] = 1
        self.hlit = max(257, _last_used(self.lit_len))
        self.hdist = max(1, _last_used(self.dst_len))
        self.items = cl_encode(self.lit_len[:self.hlit]
                               + self.dst_len[:self.hdist])
        cl_freq = [0] * T.CL_SYMBOLS
        for sym, _v, _n in self.items:
            cl_freq[sym] += 1
        self.cl_len = huffman.code_lengths(cl_freq, T.CL_MAX_LENGTH)
        self.hclen = T.CL_SYMBOLS
        while (self.hclen > 4
               and self.cl_len[T.CL_ORDER[self.hclen - 1]] == 0):
            self.hclen -= 1
        header = 5 + 5 + 4 + 3 * self.hclen
        for sym, _v, nbits in self.items:
            header += self.cl_len[sym] + nbits
        self.bits = 3 + header + _body_bits(lit_freq, dst_freq, extra,
                                            self.lit_len, self.dst_len)


def _last_used(lengths):
    for s in range(len(lengths) - 1, -1, -1):
        if lengths[s]:
            return s + 1
    return 0


# --------------------------------------------------------------
# 내보내기
def _write_body(w, tokens, lit_len, lit_code, dst_len, dst_code):
    for t in tokens:
        if isinstance(t, tuple):
            ln, d = t
            code = T.LENGTH_CODE[ln]
            w.write_code(lit_code[code], lit_len[code])
            idx = code - 257
            if T.LENGTH_EXTRA[idx]:
                w.write_bits(ln - T.LENGTH_BASE[idx],
                             T.LENGTH_EXTRA[idx])
            dc = T.dist_code(d)
            w.write_code(dst_code[dc], dst_len[dc])
            if T.DIST_EXTRA[dc]:
                w.write_bits(d - T.DIST_BASE[dc], T.DIST_EXTRA[dc])
        else:
            w.write_code(lit_code[t], lit_len[t])
    w.write_code(lit_code[T.END_OF_BLOCK], lit_len[T.END_OF_BLOCK])


def _write_stored(w, data, final):
    w.write_bits(final, 1)
    w.write_bits(STORED, 2)
    w.align()
    w.write_bits(len(data), 16)
    w.write_bits(len(data) ^ 0xFFFF, 16)
    for b in data:
        w.write_bits(b, 8)


def deflate_raw(src):
    w = bitio.LsbWriter()
    if not src:
        # 마지막 고정 블록 하나, 안에는 블록 끝 기호뿐. 두 바이트 03 00.
        w.write_bits(1, 1)
        w.write_bits(FIXED, 2)
        w.write_code(0, 7)
        w.flush()
        return w.bytes()

    tokens = parse(src)
    blocks = split_blocks(tokens)
    fixed_code = huffman.canonical_codes(T.FIXED_LITLEN)
    fixed_dcode = huffman.canonical_codes(T.FIXED_DIST)
    for k, (ta, tb, ia, ib) in enumerate(blocks):
        final = 1 if k == len(blocks) - 1 else 0
        part = tokens[ta:tb]
        lit_freq, dst_freq, extra = _freqs(part)
        raw = src[ia:ib]
        # stored 의 값은 지금 비트 자리에 달려 있다 — 정렬 때문이다.
        pad = (-(w.bit_pos() + 3)) % 8
        cost_stored = 3 + pad + 32 + 8 * len(raw)
        cost_fixed = 3 + _body_bits(lit_freq, dst_freq, extra,
                                    T.FIXED_LITLEN, T.FIXED_DIST)
        plan = DynamicPlan(lit_freq, dst_freq, extra)
        # 같으면 stored → fixed → dynamic 순. 값을 어림하면 언어마다
        # 반올림이 달라져 블록 종류가 갈린다. 그래서 정확히 센다.
        if cost_stored <= cost_fixed and cost_stored <= plan.bits:
            _write_stored(w, raw, final)
            continue
        w.write_bits(final, 1)
        if cost_fixed <= plan.bits:
            w.write_bits(FIXED, 2)
            _write_body(w, part, T.FIXED_LITLEN, fixed_code,
                        T.FIXED_DIST, fixed_dcode)
            continue
        w.write_bits(DYNAMIC, 2)
        w.write_bits(plan.hlit - 257, 5)
        w.write_bits(plan.hdist - 1, 5)
        w.write_bits(plan.hclen - 4, 4)
        for i in range(plan.hclen):
            w.write_bits(plan.cl_len[T.CL_ORDER[i]], 3)
        cl_code = huffman.canonical_codes(plan.cl_len)
        for sym, val, nbits in plan.items:
            w.write_code(cl_code[sym], plan.cl_len[sym])
            if nbits:
                w.write_bits(val, nbits)
        _write_body(w, part, plan.lit_len,
                    huffman.canonical_codes(plan.lit_len),
                    plan.dst_len, huffman.canonical_codes(plan.dst_len))
    w.flush()
    return w.bytes()


inflate_raw = inflate.inflate_raw


# ------------------------------------------------------------ 골든 코덱
# 다른 모듈과 달리 varint 헤더가 없다. 남의 형식이라 우리가 얹을 자리가
# 없기 때문이다 — 원본 길이는 스트림 자신이 알고 있다.
def encode(src):
    return deflate_raw(src)


def decode(src):
    return inflate.inflate_raw(src)
