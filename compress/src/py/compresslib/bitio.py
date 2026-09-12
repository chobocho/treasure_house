# -*- coding: utf-8 -*-
"""비트 writer/reader — SPEC §1.

이 덱에서 두 가지 비트 순서를 다 쓴다. 우리가 만드는 형식은 전부
MSB 먼저이고, DEFLATE 만 LSB 먼저다. 둘은 바꿔 쓸 수 없다.

가장 자주 갈라지는 자리는 flush 의 채움이다. **채움은 0 비트**이고,
쌓인 비트가 없으면 바이트를 내보내지 않는다. 1로 채우는 구현도
자기들끼리는 왕복이 되니, 골든 벡터를 맞춰 보기 전에는 아무도 모른다.

읽기·쓰기 모두 비트 하나당 O(1).
"""
from compresslib import varint


class MsbWriter:
    """첫 비트가 첫 바이트의 7번 비트에 앉는 writer."""

    def __init__(self):
        self._out = bytearray()
        self._buf = 0
        self._n = 0

    def write_bit(self, bit):
        self._buf |= (bit & 1) << (7 - self._n)
        self._n += 1
        if self._n == 8:
            self._out.append(self._buf)
            self._buf = 0
            self._n = 0

    def write_bits(self, value, count):
        """값의 낮은 count 비트를 높은 쪽부터 쓴다."""
        for i in range(count - 1, -1, -1):
            self.write_bit((value >> i) & 1)

    # MSB 먼저인 스트림에서는 값도 부호도 같은 순서다. 이름만 따로 둔
    # 것은 LsbWriter 와 쓰는 쪽 코드를 똑같이 만들기 위해서다.
    write_code = write_bits

    def flush(self):
        if self._n:
            self._out.append(self._buf)
            self._buf = 0
            self._n = 0

    def bytes(self):
        return bytes(self._out)


class MsbReader:
    """MsbWriter 가 쓴 것을 그대로 되읽는다."""

    def __init__(self, src, pos=0):
        self.src = src
        self.pos = pos
        self._buf = 0
        self._n = 0

    def read_bit(self):
        if self._n == 0:
            if self.pos >= len(self.src):
                raise ValueError('비트 스트림이 바닥났다')
            self._buf = self.src[self.pos]
            self.pos += 1
            self._n = 8
        self._n -= 1
        return (self._buf >> self._n) & 1

    def read_bits(self, count):
        value = 0
        for _ in range(count):
            value = (value << 1) | self.read_bit()
        return value

    def align(self):
        """바이트 경계까지 버린다 (DEFLATE 의 stored 블록에서 쓴다)."""
        self._n = 0


class LsbWriter:
    """첫 비트가 첫 바이트의 0번 비트에 앉는 writer — DEFLATE 용."""

    def __init__(self):
        self._out = bytearray()
        self._buf = 0
        self._n = 0

    def write_bit(self, bit):
        self._buf |= (bit & 1) << self._n
        self._n += 1
        if self._n == 8:
            self._out.append(self._buf)
            self._buf = 0
            self._n = 0

    def write_bits(self, value, count):
        """헤더 칸·여분 비트 — 낮은 비트부터."""
        for i in range(count):
            self.write_bit((value >> i) & 1)

    def write_code(self, code, count):
        """허프만 부호 — 같은 LSB 스트림에 높은 비트부터 넣는다.

        RFC 1951 의 가장 헷갈리는 한 줄이다. 스트림은 LSB 먼저인데
        부호만 MSB 먼저다. 두 함수로 갈라 두면 부르는 쪽이 안 헷갈린다.
        """
        for i in range(count - 1, -1, -1):
            self.write_bit((code >> i) & 1)

    def flush(self):
        if self._n:
            self._out.append(self._buf)
            self._buf = 0
            self._n = 0

    def align(self):
        """바이트 경계까지 0으로 채운다 — stored 블록 앞에서."""
        self.flush()

    def bytes(self):
        return bytes(self._out)


class LsbReader:

    def __init__(self, src, pos=0):
        self.src = src
        self.pos = pos
        self._buf = 0
        self._n = 0

    def read_bit(self):
        if self._n == 0:
            if self.pos >= len(self.src):
                raise ValueError('비트 스트림이 바닥났다')
            self._buf = self.src[self.pos]
            self.pos += 1
            self._n = 8
        bit = self._buf & 1
        self._buf >>= 1
        self._n -= 1
        return bit

    def read_bits(self, count):
        value = 0
        for i in range(count):
            value |= self.read_bit() << i
        return value

    def align(self):
        self._n = 0


# ------------------------------------------------------------ 골든 코덱
# SPEC §1.4. 압축기가 아니라 "비트 writer 가 진짜로 비트 단위로 도는가"
# 를 골든 벡터로 묶어 두기 위한 껍데기다. 앞의 0비트 셋이 요점 — 모든
# 바이트를 바이트 경계 밖으로 밀어내므로, 몰래 memcpy 하는 구현은 다른
# 파일을 낸다.
PAD_BITS = 3


def encode(src):
    w = MsbWriter()
    w.write_bits(0, PAD_BITS)
    for b in src:
        w.write_bits(b, 8)
    w.flush()
    return varint.put(len(src)) + w.bytes()


def decode(src):
    n, pos = varint.get_length(src)
    r = MsbReader(src, pos)
    r.read_bits(PAD_BITS)
    return bytes(r.read_bits(8) for _ in range(n))
