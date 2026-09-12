# -*- coding: utf-8 -*-
"""캐노니컬 허프만 — SPEC §5.

트리를 만들지 않는다. 빈도 벡터에서 **길이 벡터** 를 바로 구하고,
길이에서 부호를 규칙으로 만든다. 왜 그렇게 하는가:

  · 최적 길이 벡터는 하나가 아니다. 5,2,1 은 (1,2,2) 뿐이지만 1,1,1,1 은
    두 벌이 다 최적이다. 트리를 만들면 우선순위 큐의 동점 처리가
    어느 쪽을 고를지 정하는데, 그 처리는 언어마다 다르다.
  · 길이만 보내면 표도 작아진다. 받는 쪽이 같은 규칙으로 부호를 다시
    만들기 때문이다. DEFLATE 의 동적 블록이 이걸로 산다.

길이는 package–merge 로 구한다. 정렬 키 (무게, 종류, 순번) 가 동점 처리
전부이고, 그 키 덕분에 결과가 빈도 벡터만의 함수가 된다.

package–merge 는 O(제한 × 기호 수 log 기호 수). 15 × 256 이라 가볍다.
진짜 DEFLATE 부호기는 블록마다 이걸 돌리기가 아까워서 더 싼 보정 루프
(zlib 의 gen_bitlen)를 쓴다 — 9부에서 견준다.
"""
from compresslib import bitio, varint

MAX_LENGTH = 15
ALPHABET = 256
TABLE_BYTES = ALPHABET // 2          # 니블 하나씩 = 128바이트


def code_lengths(freqs, limit=MAX_LENGTH):
    """빈도 벡터 → 같은 길이의 길이 벡터. 안 쓰는 기호는 0.

    알파벳 크기는 freqs 의 길이가 정한다. 골든 코덱은 256 이지만
    DEFLATE 동적 블록은 286·30·19 세 가지를 쓴다.
    """
    used = [(f, s) for s, f in enumerate(freqs) if f]
    used.sort()
    m = len(used)
    lengths = [0] * len(freqs)
    if m == 0:
        return lengths
    if m == 1:
        lengths[used[0][1]] = 1
        return lengths
    if m > (1 << limit):
        raise ValueError('기호 %d개는 길이 %d 로 못 담는다'
                         % (m, limit))

    # 동전 하나 = (무게, 종류, 순번, 이 동전이 품은 기호 목록). 종류 0
    # 이 기호 동전, 1 이 꾸러미다 — 무게가 같으면 기호 동전이 앞선다.
    coins = [(f, 0, j, (s,)) for j, (f, s) in enumerate(used)]
    level = coins
    for _ in range(limit - 1):
        packed = [(level[2 * i][0] + level[2 * i + 1][0], 1, i,
                   level[2 * i][3] + level[2 * i + 1][3])
                  for i in range(len(level) // 2)]
        level = sorted(packed + coins)

    for _w, _k, _r, syms in level[:2 * m - 2]:
        for s in syms:
            lengths[s] += 1
    return lengths


def canonical_codes(lengths):
    """길이 벡터 → 부호 벡터. RFC 1951 §3.2.2 와 같은 규칙."""
    bl_count = [0] * (MAX_LENGTH + 1)
    for l in lengths:
        if l:
            if l > MAX_LENGTH:
                raise ValueError('길이 %d 는 상한 %d 를 넘는다'
                                 % (l, MAX_LENGTH))
            bl_count[l] += 1
    code = 0
    next_code = [0] * (MAX_LENGTH + 2)
    for bits in range(1, MAX_LENGTH + 1):
        code = (code + bl_count[bits - 1]) << 1
        next_code[bits] = code
    codes = [0] * len(lengths)
    for s in range(len(lengths)):
        l = lengths[s]
        if l:
            if next_code[l] >= (1 << l):
                raise ValueError('부호표가 넘친다 — 길이 %d' % l)
            codes[s] = next_code[l]
            next_code[l] += 1
    return codes


def check_complete(lengths, max_length=MAX_LENGTH):
    """크래프트 합이 1 인지. 넘치면 못 푸는 표, 모자라면 손상된 표다.

    예외가 하나 있다. **기호가 하나뿐인 표** 는 길이 1 짜리 부호 하나라
    합이 1/2 이고, 그래서 늘 "모자란" 표다. zeros_64k.bin 처럼 한 가지
    바이트만 있는 파일에서 반드시 나오는 모양이라 받아 준다. 이때
    복호기는 기호마다 비트 하나를 읽고, 1 이 나오면 손상으로 본다.
    (RFC 1951 도 거리표 하나짜리에 같은 예외를 둔다 — 9부에서 본다.)
    """
    used = [l for l in lengths if l]
    total = sum(1 << (max_length - l) for l in used)
    full = 1 << max_length
    if total > full:
        raise ValueError('부호표가 넘친다 (크래프트 합 > 1)')
    if total < full:
        if len(used) == 1 and used[0] == 1:
            return
        raise ValueError('부호표가 모자란다 (크래프트 합 < 1)')


class Decoder:
    """캐노니컬 복호기 — 트리를 안 만든다.

    길이별 첫 부호와 첫 자리만 있으면 비트를 하나씩 받아 가며 판정할 수
    있다. 메모리 O(길이 상한), 기호 하나당 O(부호 길이).
    """

    def __init__(self, lengths, max_length=MAX_LENGTH):
        self.max_length = max_length
        self.symbols = sorted((l, s)
                              for s, l in enumerate(lengths) if l)
        self.count = [0] * (max_length + 1)
        for l, _s in self.symbols:
            self.count[l] += 1
        self.first_code = [0] * (max_length + 2)
        self.first_index = [0] * (max_length + 2)
        code = index = 0
        for l in range(1, max_length + 1):
            code = (code + self.count[l - 1]) << 1
            self.first_code[l] = code
            self.first_index[l] = index
            index += self.count[l]

    def read(self, r):
        code = 0
        for l in range(1, self.max_length + 1):
            code = (code << 1) | r.read_bit()
            off = code - self.first_code[l]
            if self.count[l] and off < self.count[l]:
                i = self.first_index[l] + off
                return self.symbols[i][1]
        raise ValueError('부호표에 없는 비트열')


# ------------------------------------------------------------ 골든 코덱
# SPEC §5.3. 표는 기호 하나에 니블 하나, 언제나 128바이트다. 세 기호만
# 쓰는 파일에도 128바이트가 붙는다 — 헤더를 줄이는 이야기가 9부의 동적
# 블록이다.


def nibble(table, sym):
    """128바이트 표에서 기호 하나의 길이를 꺼낸다. 짝수는 높은 니블."""
    b = table[sym >> 1]
    return (b >> 4) if (sym & 1) == 0 else (b & 0x0F)


def pack_table(lengths):
    table = bytearray(TABLE_BYTES)
    for s in range(ALPHABET):
        if s & 1:
            table[s >> 1] |= lengths[s] & 0x0F
        else:
            table[s >> 1] |= (lengths[s] & 0x0F) << 4
    return bytes(table)


def encode(src):
    if not src:
        return varint.put(0)
    freqs = [0] * ALPHABET
    for b in src:
        freqs[b] += 1
    lengths = code_lengths(freqs)
    codes = canonical_codes(lengths)
    w = bitio.MsbWriter()
    for b in src:
        w.write_bits(codes[b], lengths[b])
    w.flush()
    return varint.put(len(src)) + pack_table(lengths) + w.bytes()


def decode(src):
    n, pos = varint.get_length(src)
    if n == 0:
        if pos != len(src):
            raise ValueError('빈 입력인데 뒤에 바이트가 있다')
        return b''
    if len(src) < pos + TABLE_BYTES:
        raise ValueError('부호 길이 표가 잘렸다')
    table = src[pos:pos + TABLE_BYTES]
    lengths = [nibble(table, s) for s in range(ALPHABET)]
    check_complete(lengths)
    dec = Decoder(lengths)
    r = bitio.MsbReader(src, pos + TABLE_BYTES)
    return bytes(dec.read(r) for _ in range(n))
