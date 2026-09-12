# -*- coding: utf-8 -*-
"""inflate — RFC 1951 복호기 (SPEC §10.7).

부호기보다 복호기가 먼저다. 형식을 읽을 줄 알아야 내가 쓴 것이 맞는지
알 수 있고, 무엇보다 **진짜 gzip 이 만든 파일** 을 풀 수 있어야 한다.
그것이 "우리가 DEFLATE 를 구현했다" 는 말의 유일한 증거다.

받아 주면 안 되는 것들을 일부러 나열해 둔다(§10.7). 손상된 파일을 조용히
넘기는 복호기는 압축에서 특히 위험하다 — 아무거나 그럴듯한 바이트가
나오기 때문이다.

예외 하나: 거리 부호가 하나뿐인 표는 크래프트 합이 1/2 라 "모자란"
표인데, RFC 가 허용하고 zlib 도 낸다. 일치 없는 블록에서 나온다.
"""
from compresslib import bitio, huffman
from compresslib import deflate_tables as T

MAX_BLOCK_STORED = 0xFFFF


def _table(lengths):
    huffman.check_complete(lengths)
    return huffman.Decoder(lengths)


def _read_dynamic_header(r):
    """동적 블록의 두 표를 읽는다. (리터럴·길이 복호기, 거리 복호기)."""
    hlit = r.read_bits(5) + 257
    hdist = r.read_bits(5) + 1
    hclen = r.read_bits(4) + 4
    if hlit > T.LITLEN_SYMBOLS or hdist > T.DIST_SYMBOLS:
        raise ValueError('HLIT/HDIST 가 알파벳을 넘는다')
    cl_lengths = [0] * T.CL_SYMBOLS
    for i in range(hclen):
        cl_lengths[T.CL_ORDER[i]] = r.read_bits(3)
    cl = _table(cl_lengths)

    lengths = []
    want = hlit + hdist
    while len(lengths) < want:
        sym = cl.read(r)
        if sym < 16:
            lengths.append(sym)
        elif sym == T.CL_REPEAT:
            if not lengths:
                raise ValueError('부호 16 이 맨 앞에 왔다')
            lengths += [lengths[-1]] * (r.read_bits(2) + 3)
        elif sym == T.CL_ZERO_SHORT:
            lengths += [0] * (r.read_bits(3) + 3)
        else:
            lengths += [0] * (r.read_bits(7) + 11)
    if len(lengths) != want:
        raise ValueError('부호 길이 되풀이가 표 끝을 넘었다')
    return _table(lengths[:hlit]), _table(lengths[hlit:])


def _read_block_body(r, out, litlen, dist):
    while True:
        sym = litlen.read(r)
        if sym < 256:
            out.append(sym)
            continue
        if sym == T.END_OF_BLOCK:
            return
        idx = sym - 257
        if idx >= len(T.LENGTH_SPEC):
            raise ValueError('길이 부호 %d 는 없다' % sym)
        length = T.LENGTH_BASE[idx] + r.read_bits(T.LENGTH_EXTRA[idx])
        dcode = dist.read(r)
        if dcode >= T.DIST_SYMBOLS:
            raise ValueError('거리 부호 %d 는 쓰이지 않는다' % dcode)
        d = T.DIST_BASE[dcode] + r.read_bits(T.DIST_EXTRA[dcode])
        if d > len(out):
            raise ValueError('거리 %d 가 지금까지 낸 것보다 멀다' % d)
        start = len(out) - d
        # 한 바이트씩 앞으로. 거리 1 짜리 긴 일치가 여기 기댄다.
        for k in range(length):
            out.append(out[start + k])


def inflate_raw(src):
    r = bitio.LsbReader(src)
    out = bytearray()
    fixed_litlen = fixed_dist = None
    while True:
        final = r.read_bits(1)
        btype = r.read_bits(2)
        if btype == 0:
            r.align()
            if r.pos + 4 > len(src):
                raise ValueError('stored 블록 머리가 잘렸다')
            ln = src[r.pos] | (src[r.pos + 1] << 8)
            nln = src[r.pos + 2] | (src[r.pos + 3] << 8)
            r.pos += 4
            if ln != (nln ^ 0xFFFF):
                raise ValueError('NLEN 이 LEN 의 보수가 아니다')
            if r.pos + ln > len(src):
                raise ValueError('stored 블록 몸통이 잘렸다')
            out += src[r.pos:r.pos + ln]
            r.pos += ln
        elif btype == 1:
            if fixed_litlen is None:
                fixed_litlen = _table(T.FIXED_LITLEN)
                fixed_dist = _table(T.FIXED_DIST)
            _read_block_body(r, out, fixed_litlen, fixed_dist)
        elif btype == 2:
            litlen, dist = _read_dynamic_header(r)
            _read_block_body(r, out, litlen, dist)
        else:
            raise ValueError('BTYPE 11 은 없는 블록 종류다')
        if final:
            return bytes(out)
