# -*- coding: utf-8 -*-
"""이진 레인지 코더 — SPEC §8.

허프만은 기호 하나에 **정수** 비트를 쓴다. 확률 0.9 인 기호도 최소
1비트라, 0.15비트면 될 자리에 1비트를 쓴다. 레인지 코더에는 그 제약이
없다 — 구간 [low, low+range) 를 확률대로 쪼개 들어가기만 하면 된다.

대가는 둘이다. 구간이 좁아지면 위 바이트부터 내보내야 하고(정규화),
low 에 더하다 올림이 나면 이미 내보낸 바이트를 고쳐야 한다(캐리 전파).
캐리를 "아직 안 내보낸 0xFF 가 몇 개" 로 세어 두는 것이 shift_low 다.

LZMA 의 것을 그대로 쓴다. 14번 모듈이 진짜 .lzma 를 풀어야 하는데,
코더를 둘 두면 맞출 것이 두 배가 된다. 그래서 스트림 첫 바이트가 늘
0 인 것까지 LZMA 와 같다 — 첫 바이트에 올 수 있었던 캐리의 자리다.

파이썬은 정수가 무한이라 **아무것도 넘치지 않는다.** 그래서 넘침으로
알려 주는 것이 없고, 마스크를 빠뜨려도 조용히 다른 답을 낸다. 다섯 언어
가운데 여기서 틀리기 가장 쉬운 것이 파이썬이다 (SPEC §8.4).
"""
from compresslib import varint

PROB_BITS = 11
PROB_TOTAL = 1 << PROB_BITS          # 2048
PROB_INIT = PROB_TOTAL // 2          # 1024 = 확률 1/2
MOVE_BITS = 5
TOP = 1 << 24
U32 = 0xFFFFFFFF


class Encoder:

    def __init__(self):
        self.low = 0                 # 최대 2^33 — 32비트가 아니다
        self.range = U32
        self.cache = 0
        self.cache_size = 1
        self._out = bytearray()

    def shift_low(self):
        """위 바이트 하나를 확정해 내보낸다. 캐리는 앞으로 전파한다."""
        if (self.low >> 32) or self.low < 0xFF000000:
            carry = self.low >> 32
            temp = self.cache
            while True:
                self._out.append((temp + carry) & 0xFF)
                temp = 0xFF
                self.cache_size -= 1
                if self.cache_size == 0:
                    break
            self.cache = (self.low >> 24) & 0xFF
        self.cache_size += 1
        self.low = (self.low << 8) & U32

    def encode_bit(self, probs, i, bit):
        bound = (self.range >> PROB_BITS) * probs[i]
        if bit == 0:
            self.range = bound
            probs[i] += (PROB_TOTAL - probs[i]) >> MOVE_BITS
        else:
            self.low += bound
            self.range -= bound
            probs[i] -= probs[i] >> MOVE_BITS
        while self.range < TOP:
            self.range = (self.range << 8) & U32
            self.shift_low()

    def encode_freq(self, cum, freq, tot):
        """빈도 표에서 기호 하나를 적는다 (SPEC §17.2).

        §8 의 비트 부호기와 스트림도 정규화도 같이 쓴다 — 모델이 둘을
        섞어 써도 된다. tot 는 2^16 아래여야 r 이 0 이 되지 않는다.
        """
        r = self.range // tot
        self.low += r * cum
        self.range = r * freq
        while self.range < TOP:
            self.range = (self.range << 8) & U32
            self.shift_low()

    def flush(self):
        for _ in range(5):
            self.shift_low()

    def bytes(self):
        return bytes(self._out)


class Decoder:

    def __init__(self, src, pos=0):
        self.src = src
        self.pos = pos
        self.range = U32
        self.code = 0
        if pos >= len(src):
            raise ValueError('레인지 코더 스트림이 비었다')
        if src[pos] != 0:
            raise ValueError('첫 바이트가 0 이 아니다: %d' % src[pos])
        self.pos += 1
        for _ in range(4):
            self.code = ((self.code << 8) | self._byte()) & U32

    def _byte(self):
        # 잘 만들어진 스트림도 마지막 판정에서 한 바이트쯤 더 읽는다.
        # 끝을 넘겨 다섯 바이트까지는 0 으로 봐 주고, 그보다 가면
        # 손상이다.
        if self.pos < len(self.src):
            b = self.src[self.pos]
            self.pos += 1
            return b
        self.pos += 1
        if self.pos > len(self.src) + 5:
            raise ValueError('스트림 끝을 너무 많이 넘었다')
        return 0

    def decode_freq(self, tot):
        """지금 자리가 [0, tot) 가운데 어디인지 (SPEC §17.2).

        이 값으로 기호를 찾고, 그 기호의 (cum, freq) 로 decode_update 를
        불러야 한다. 둘로 나뉜 것은 "무엇인지 알아야 얼마나 좁힐지 안다"
        는 순서 때문이다.
        """
        r = self.range // tot
        v = self.code // r
        return tot - 1 if v >= tot else v

    def decode_update(self, cum, freq, tot):
        r = self.range // tot
        self.code = (self.code - r * cum) & U32
        self.range = r * freq
        while self.range < TOP:
            self.range = (self.range << 8) & U32
            self.code = ((self.code << 8) | self._byte()) & U32

    def decode_bit(self, probs, i):
        bound = (self.range >> PROB_BITS) * probs[i]
        if self.code < bound:
            self.range = bound
            probs[i] += (PROB_TOTAL - probs[i]) >> MOVE_BITS
            bit = 0
        else:
            self.code -= bound
            self.range -= bound
            probs[i] -= probs[i] >> MOVE_BITS
            bit = 1
        while self.range < TOP:
            self.range = (self.range << 8) & U32
            self.code = ((self.code << 8) | self._byte()) & U32
        return bit


    def decode_direct_bits(self, count):
        """확률 모델 없이 비트를 그대로 읽는다 (SPEC §16.5).

        LZMA 의 먼 거리는 가운데 비트를 모델링하지 않는다 — 어차피
        반반이라 얻는 것이 없다. t 는 "code 가 음수가 됐으면 되돌리고
        0 비트를 낸다" 를 분기 없이 쓴 것이고, code 가 **부호 없는
        32비트** 라는 데 기댄다.
        """
        result = 0
        for _ in range(count):
            self.range >>= 1
            self.code = (self.code - self.range) & U32
            t = 0 - (self.code >> 31)
            self.code = (self.code + (self.range & t)) & U32
            if self.range < TOP:
                self.range = (self.range << 8) & U32
                self.code = ((self.code << 8) | self._byte()) & U32
            result = (result << 1) + ((t + 1) & 1)
        return result


class ByteModel:
    """0차 적응 바이트 모델 — 확률 256칸을 이진 트리처럼 쓴다.

    문맥은 1 에서 시작해 비트 하나마다 (ctx<<1)|bit 로 내려간다. 여덟 번
    지나면 256..511 이 되므로 실제로 쓰이는 자리는 1..255 뿐이고,
    0번 칸은 한 번도 안 쓴다. 그래서 배열이 257 이 아니라 256 이다.
    """

    def __init__(self):
        self.probs = [PROB_INIT] * 256

    def encode(self, enc, b):
        ctx = 1
        for i in range(7, -1, -1):
            bit = (b >> i) & 1
            enc.encode_bit(self.probs, ctx, bit)
            ctx = (ctx << 1) | bit

    def decode(self, dec):
        ctx = 1
        for _ in range(8):
            ctx = (ctx << 1) | dec.decode_bit(self.probs, ctx)
        return ctx - 256


# ------------------------------------------------------------ 골든 코덱
def encode(src):
    if not src:
        return varint.put(0)
    enc = Encoder()
    m = ByteModel()
    for b in src:
        m.encode(enc, b)
    enc.flush()
    return varint.put(len(src)) + enc.bytes()


def decode(src):
    n, pos = varint.get_length(src)
    if n == 0:
        if pos != len(src):
            raise ValueError('빈 입력인데 뒤에 바이트가 있다')
        return b''
    dec = Decoder(src, pos)
    m = ByteModel()
    return bytes(m.decode(dec) for _ in range(n))
