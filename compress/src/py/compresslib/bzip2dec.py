# -*- coding: utf-8 -*-
"""bzip2 복호기 — SPEC §15.

bzip2 가 쓰는 조각은 이미 다 있다. BWT(§9)·MTF(§4)·0런(§3.2)·캐노니컬
허프만(§5). bzip2 가 더한 것은 **조립** 이다 — 부호기는 안 만든다.
부호기를 만들면 또 우리 선택을 시험하는 꼴이고, **진짜 bzip2 가 만든
파일을 푸는 것** 이 훨씬 센 주장이기 때문이다.

파이프라인을 거꾸로 밟는다:
    허프만 → RUNA/RUNB 풀기 → MTF 역변환 → BWT 역변환 → RLE1 풀기

가장 잘 속는 자리는 CRC 다. bzip2 의 CRC-32 는 gzip 것과 다항식은
같아도 **반사가 없다.** gzip 표를 쓰면 빈 입력만 맞고 나머지는 전부
틀리는데, 왕복 시험으로는 절대 안 드러난다 (§15.6).

시간은 블록 크기 m 에 대해 O(m), 공간도 O(m).
"""
from compresslib import bwt, huffman

MAGIC = b'BZh'
BLOCK_MAGIC = 0x314159265359
END_MAGIC = 0x177245385090
MAX_GROUPS = 6
GROUP_SIZE = 50
MAX_CODE_LEN = 20
MAX_ALPHA = 258            # 기호 256 + RUNA/RUNB 자리
RUNA, RUNB = 0, 1


def _make_crc_table():
    """반사 없는 CRC-32/BZIP2 표. 0x04C11DB7 을 위에서부터 민다."""
    table = []
    for i in range(256):
        c = i << 24
        for _ in range(8):
            c = ((c << 1) ^ 0x04C11DB7) & 0xFFFFFFFF if c & 0x80000000 \
                else (c << 1) & 0xFFFFFFFF
        table.append(c)
    return table


CRC_TABLE = _make_crc_table()


def crc32_bzip2(data):
    c = 0xFFFFFFFF
    for b in data:
        c = CRC_TABLE[((c >> 24) ^ b) & 0xFF] ^ ((c << 8) & 0xFFFFFFFF)
    return c ^ 0xFFFFFFFF


class BitReader:
    """MSB 먼저. bzip2 는 48비트 매직이 있어 넓은 읽기가 필요하다."""

    def __init__(self, src, pos=0):
        self.src = src
        self.pos = pos
        self.buf = 0
        self.n = 0

    def read_bit(self):
        if self.n == 0:
            if self.pos >= len(self.src):
                raise ValueError('bzip2 스트림이 바닥났다')
            self.buf = self.src[self.pos]
            self.pos += 1
            self.n = 8
        self.n -= 1
        return (self.buf >> self.n) & 1

    def read_bits(self, count):
        v = 0
        for _ in range(count):
            v = (v << 1) | self.read_bit()
        return v


def rle1_decode(src):
    """같은 바이트 넷 뒤의 한 바이트는 "더 붙일 개수" 다 (§15.5)."""
    out = bytearray()
    i = 0
    n = len(src)
    while i < n:
        b = src[i]
        run = 1
        while run < 4 and i + run < n and src[i + run] == b:
            run += 1
        out += bytes([b]) * run
        i += run
        if run == 4:
            if i >= n:
                raise ValueError('RLE1 의 개수 바이트가 없다')
            out += bytes([b]) * src[i]
            i += 1
    return bytes(out)


def _read_symbol_map(r):
    """쓰인 바이트 값 목록. 16개 묶음의 있음/없음을 먼저 읽는다."""
    used = []
    groups = r.read_bits(16)
    for g in range(16):
        if groups & (1 << (15 - g)):
            bits = r.read_bits(16)
            for k in range(16):
                if bits & (1 << (15 - k)):
                    used.append(g * 16 + k)
    if not used:
        raise ValueError('기호 지도가 비었다')
    return used


def _read_selectors(r, n_groups, n_selectors):
    """단항으로 적힌 MTF 선택자. 값이 곧 "몇 번째 표" 다."""
    mtf = list(range(n_groups))
    out = []
    for _ in range(n_selectors):
        j = 0
        while r.read_bit():
            j += 1
            if j >= n_groups:
                raise ValueError('선택자가 표 개수를 넘는다')
        v = mtf.pop(j)
        mtf.insert(0, v)
        out.append(v)
    return out


def _read_tables(r, n_groups, alpha_size):
    tables = []
    for _ in range(n_groups):
        length = r.read_bits(5)
        lengths = []
        for _s in range(alpha_size):
            while True:
                if not 1 <= length <= MAX_CODE_LEN:
                    raise ValueError('부호 길이가 범위 밖이다: %d'
                                     % length)
                if not r.read_bit():
                    break
                length += -1 if r.read_bit() else 1
            lengths.append(length)
        huffman.check_complete(lengths, MAX_CODE_LEN)
        tables.append(huffman.Decoder(lengths, MAX_CODE_LEN))
    return tables


def _read_block_symbols(r, tables, selectors, alpha_size, limit):
    """허프만 → MTF 지표 열. RUNA/RUNB 는 여기서 0 의 런으로 편다."""
    eob = alpha_size - 1
    out = []
    group = 0
    left = 0
    dec = None
    run = 0
    weight = 1
    while True:
        if left == 0:
            if group >= len(selectors):
                raise ValueError('선택자가 모자란다')
            dec = tables[selectors[group]]
            group += 1
            left = GROUP_SIZE
        left -= 1
        sym = dec.read(r)
        if sym <= RUNB:
            run += (sym + 1) * weight
            weight <<= 1
            if run > limit:
                raise ValueError('0 런이 블록 크기를 넘는다')
            continue
        if run:
            out += [0] * run
            run = 0
            weight = 1
        if sym == eob:
            return out
        out.append(sym - 1)
        if len(out) > limit:
            raise ValueError('블록이 상한을 넘는다')


def _inverse_mtf(indices, used):
    """쓰인 값만 놓고 MTF 를 되돌린다 — 기호 지도가 여기서 값을 한다."""
    table = list(used)
    out = bytearray()
    for i in indices:
        if i >= len(table):
            raise ValueError('MTF 지표가 알파벳을 넘는다')
        v = table[i]
        out.append(v)
        if i:
            del table[i]
            table.insert(0, v)
    return bytes(out)


def decode(src):
    if len(src) < 4 or src[:3] != MAGIC:
        raise ValueError('bzip2 매직이 아니다')
    level = src[3] - 0x30
    if not 1 <= level <= 9:
        raise ValueError('블록 크기 등급이 1~9 가 아니다: %d' % level)
    limit = level * 100000
    r = BitReader(src, 4)
    out = bytearray()
    combined = 0
    while True:
        magic = r.read_bits(48)
        if magic == END_MAGIC:
            want = r.read_bits(32)
            if want != combined:
                raise ValueError('합친 CRC 가 다르다')
            return bytes(out)
        if magic != BLOCK_MAGIC:
            raise ValueError('블록 매직이 아니다')
        block_crc = r.read_bits(32)
        if r.read_bit():
            raise ValueError('무작위화된 블록은 지원하지 않는다')
        orig_ptr = r.read_bits(24)
        used = _read_symbol_map(r)
        alpha_size = len(used) + 2
        n_groups = r.read_bits(3)
        if not 2 <= n_groups <= MAX_GROUPS:
            raise ValueError('표 개수가 2~6 이 아니다: %d' % n_groups)
        n_selectors = r.read_bits(15)
        selectors = _read_selectors(r, n_groups, n_selectors)
        tables = _read_tables(r, n_groups, alpha_size)
        indices = _read_block_symbols(r, tables, selectors,
                                      alpha_size, limit)
        l_column = _inverse_mtf(indices, used)
        if orig_ptr >= len(l_column):
            raise ValueError('origPtr 가 블록 밖이다')
        block = bwt.inverse_block(l_column, orig_ptr)
        block = rle1_decode(block)
        got = crc32_bzip2(block)
        if got != block_crc:
            raise ValueError('블록 CRC 가 다르다')
        combined = (((combined << 1) | (combined >> 31)) & 0xFFFFFFFF) \
            ^ block_crc
        out += block
