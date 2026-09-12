# -*- coding: utf-8 -*-
"""LZ4 — SPEC §14.

LZ77 인데 **엔트로피 부호가 아예 없다.** 허프만도, 레인지 코더도, ANS 도
없이 리터럴과 일치를 바이트로 그냥 적는다. DEFLATE 보다 덜 줄고 몇 배
빨리 풀린다 — 복호기의 안쪽 고리가 memcpy 둘이고 비트 조작이 없다.
12부에서 zstd 와 나란히 놓고 그 거래를 본다.

형식이 부호기에 요구하는 꼬리 규칙 둘이 있다. 마지막 5바이트는 반드시
리터럴이고, 일치는 끝에서 12바이트 안쪽에서 시작할 수 없다. 복호기가
끝을 매번 확인하지 않고 8바이트씩 복사할 수 있게 하려는 것이고,
지키지 않으면 진짜 lz4 가 거절한다.

프레임은 **읽기만** 한다(§14.6). 내용 검사합(xxHash)은 건너뛴다 —
이 덱의 다른 어떤 것과도 무관한 알고리즘이라, 다섯 번 구현해도
압축에 대해 배울 것이 없다.

시간 O(입력 길이), 공간 O(해시 표 4096).
"""
from compresslib import varint

MIN_MATCH = 4
LAST_LITERALS = 5
MF_LIMIT = 12
HASH_LOG = 12
HASH_SIZE = 1 << HASH_LOG
HASH_MUL = 2654435761
MAX_OFFSET = 65535

FRAME_MAGIC = b'\x04\x22\x4d\x18'


def put_lsic(v):
    """선형 소정수 부호 — 255 는 "계속", 그보다 작으면 끝.

    그래서 정확히 255 는 두 바이트(255, 0)로 적힌다. 이 한 줄이 LZ4
    복호기가 분기 없이 도는 이유이자, 255 가 한 바이트로 안 되는 이유다.
    """
    out = bytearray()
    while v >= 255:
        out.append(255)
        v -= 255
    out.append(v)
    return bytes(out)


def get_lsic(src, pos):
    """(값, 다음 위치).

    고리를 묶는 것은 입력 자신이다 — 이어짐 바이트가 블록에 남은 것보다
    많을 수는 없다. 고정 상한은 솔깃하고 틀린다: 처음에 1000 으로 뒀다가
    mixed_1m.bin 의 정당한 256 KiB 일치(이어짐 1028바이트)에서 걸렸다.
    """
    total = 0
    while pos < len(src):
        b = src[pos]
        pos += 1
        total += b
        if b != 255:
            if total > varint.MAX_LENGTH:
                raise ValueError('LSIC 값이 너무 크다')
            return total, pos
    raise ValueError('LSIC 가 잘렸다')


def _hash4(src, i):
    v = (src[i] | (src[i + 1] << 8)
         | (src[i + 2] << 16) | (src[i + 3] << 24))
    return ((v * HASH_MUL) & 0xFFFFFFFF) >> (32 - HASH_LOG)


def _same4(src, a, b):
    return src[a:a + 4] == src[b:b + 4]


def _emit(out, literals, offset, length):
    """시퀀스 하나. offset 이 None 이면 마지막(리터럴만) 시퀀스다."""
    lit_len = len(literals)
    token_lit = min(lit_len, 15)
    if offset is None:
        out.append(token_lit << 4)
        if lit_len >= 15:
            out += put_lsic(lit_len - 15)
        out += literals
        return
    ml_code = length - MIN_MATCH
    token_ml = min(ml_code, 15)
    out.append((token_lit << 4) | token_ml)
    if lit_len >= 15:
        out += put_lsic(lit_len - 15)
    out += literals
    out.append(offset & 0xFF)
    out.append(offset >> 8)
    if ml_code >= 15:
        out += put_lsic(ml_code - 15)


def compress_block(src):
    n = len(src)
    out = bytearray()
    if n < MF_LIMIT + 1:
        _emit(out, src, None, 0)
        return bytes(out)
    table = [-1] * HASH_SIZE
    ip = anchor = 0
    while ip <= n - MF_LIMIT:
        h = _hash4(src, ip)
        ref = table[h]
        table[h] = ip
        if ref >= 0 and ip - ref <= MAX_OFFSET and _same4(src, ref, ip):
            ml = MIN_MATCH
            limit = n - LAST_LITERALS
            while ip + ml < limit and src[ref + ml] == src[ip + ml]:
                ml += 1
            _emit(out, src[anchor:ip], ip - ref, ml)
            ip += ml
            anchor = ip
        else:
            ip += 1
    _emit(out, src[anchor:n], None, 0)
    return bytes(out)


def parse_sequences(block):
    """(리터럴, (거리, 길이) 또는 None) 목록.

    푸는 데는 안 쓴다 — decompress_block 은 같은 일을 고리 안에서 바로
    한다. 이 함수는 **시퀀스를 눈으로 보려고** 있다: 시험이 꼬리 규칙을
    확인하는 데 쓰고, 12부의 데모가 이 목록을 그대로 그린다.
    다른 네 언어에는 없다.
    """
    out = []
    pos = 0
    n = len(block)
    while pos < n:
        token = block[pos]
        pos += 1
        lit_len = token >> 4
        if lit_len == 15:
            extra, pos = get_lsic(block, pos)
            lit_len += extra
        if pos + lit_len > n:
            raise ValueError('리터럴이 잘렸다')
        literals = block[pos:pos + lit_len]
        pos += lit_len
        if pos == n:
            out.append((literals, None))
            break
        if pos + 2 > n:
            raise ValueError('거리가 잘렸다')
        offset = block[pos] | (block[pos + 1] << 8)
        pos += 2
        ml = token & 15
        if ml == 15:
            extra, pos = get_lsic(block, pos)
            ml += extra
        out.append((literals, (offset, ml + MIN_MATCH)))
    return out


def decompress_block(block, want=None):
    out = bytearray()
    pos = 0
    n = len(block)
    while pos < n:
        token = block[pos]
        pos += 1
        lit_len = token >> 4
        if lit_len == 15:
            extra, pos = get_lsic(block, pos)
            lit_len += extra
        if pos + lit_len > n:
            raise ValueError('리터럴이 잘렸다')
        out += block[pos:pos + lit_len]
        pos += lit_len
        if pos == n:
            break                       # 마지막 시퀀스는 리터럴뿐이다
        if pos + 2 > n:
            raise ValueError('거리가 잘렸다')
        offset = block[pos] | (block[pos + 1] << 8)
        pos += 2
        length = token & 15
        if length == 15:
            extra, pos = get_lsic(block, pos)
            length += extra
        length += MIN_MATCH
        if offset == 0:
            raise ValueError('거리 0 은 없다')
        if offset > len(out):
            raise ValueError('거리 %d 가 낸 것보다 멀다' % offset)
        start = len(out) - offset
        # 한 바이트씩 앞으로. 거리 1 짜리 긴 일치가 여기 기댄다.
        for j in range(length):
            out.append(out[start + j])
    if want is not None and len(out) != want:
        raise ValueError('푼 길이가 헤더와 다르다: %d != %d'
                         % (len(out), want))
    return bytes(out)


def encode(src):
    if not src:
        return varint.put(0)
    return varint.put(len(src)) + compress_block(src)


def decode(src):
    n, pos = varint.get_length(src)
    if n == 0:
        if pos != len(src):
            raise ValueError('빈 입력인데 뒤에 바이트가 있다')
        return b''
    return decompress_block(src[pos:], n)


# --------------------------------------------------------------- 프레임
def frame_decode(src):
    """진짜 lz4 명령이 쓰는 프레임을 푼다 (§14.6). 쓰지는 않는다."""
    if len(src) < 7 or src[:4] != FRAME_MAGIC:
        raise ValueError('lz4 프레임 매직이 아니다')
    flg = src[4]
    version = flg >> 6
    if version != 1:
        raise ValueError('모르는 프레임 판: %d' % version)
    block_checksum = bool(flg & 0x10)
    content_size = bool(flg & 0x08)
    content_checksum = bool(flg & 0x04)
    dict_id = bool(flg & 0x01)
    pos = 6                                   # 매직 4 + FLG + BD
    if content_size:
        pos += 8
    if dict_id:
        pos += 4
    pos += 1                                  # 머리 검사 바이트(HC)
    out = bytearray()
    while True:
        if pos + 4 > len(src):
            raise ValueError('블록 크기가 잘렸다')
        size = int.from_bytes(src[pos:pos + 4], 'little')
        pos += 4
        if size == 0:
            break
        stored = bool(size & 0x80000000)
        size &= 0x7FFFFFFF
        if pos + size > len(src):
            raise ValueError('블록이 잘렸다')
        chunk = src[pos:pos + size]
        pos += size
        if block_checksum:
            pos += 4                          # 블록 xxHash — 건너뛴다
        out += chunk if stored else decompress_block(chunk)
    if content_checksum:
        # 내용 xxHash 4바이트. 건너뛴다 — §14.6 에 이유를 적어 뒀다.
        pos += 4
    return bytes(out)
