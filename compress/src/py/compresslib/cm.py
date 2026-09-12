# -*- coding: utf-8 -*-
"""문맥 혼합 — SPEC §18.

여기까지의 코덱은 모델을 **하나** 골랐다. PPM 도 가장 긴 문맥을 고르고
안 되면 내려갈 뿐이다. 문맥 혼합은 고르지 않는다 — 여러 모델에게
한꺼번에 묻고 **의견을 섞는다.** 그러면서 누구를 믿을지 스스로 배운다.
paq/lpaq 계보와 대용량 텍스트 벤치마크 상위권이 전부 이것이다.

여기 것은 한자리에서 읽을 만큼 작은 lpaq 모양이다 — 문맥 모델 다섯,
로지스틱 믹서 하나, APM 하나. 진짜 paq 와 겨루지 않는다. 겨루는 상대는
**자기 자신** 이고, 덱은 모델을 1~5개 켰을 때의 비율을 나란히 보인다.

섞는 자리가 요점이다. 확률을 그냥 평균 내면 0.01 과 0.99 가 0.5 가 되어
두 모델의 확신이 통째로 사라진다. **로지스틱 영역** 에서 더해야 한다.

시간은 바이트당 8비트 × 모델 5개, 공간은 표 (2^20 × 2바이트) × 4.
"""
from array import array

from compresslib import rangecoder, varint

TABLE_BITS = 20
TABLE_SIZE = 1 << TABLE_BITS
NUM_MODELS = 5
PROB_ONE = 4096
PROB_HALF = PROB_ONE // 2
# 셈이 쌓일수록 천천히 움직인다. 처음 보는 문맥은 빨리 배우고 오래 본
# 문맥은 흔들리지 않아야 한다 — 고정 비율 하나로는 둘 다 못 한다.
COUNTER_RATES = [1, 1, 2, 2, 3, 3, 4, 4, 4, 5, 5, 5, 5, 5, 5, 5]
COUNTER_LIMIT = len(COUNTER_RATES) - 1
MIXER_SHIFT = 16
MIXER_INIT = 1 << 14
# 믹서 갱신의 시프트. lpaq 과 같은 16이다. 10 으로 두면 가중치가 한
# 걸음에 5만씩 튀어 모델이 수렴하지 못한다 — 처음에 그렇게 뒀다가
# 비율이 PPM 보다 나빠서 알았다.
MIXER_UPDATE_SHIFT = 16
MIXER_LEARN = 16
MIXER_CLAMP = 1 << 20
APM_RATE = 7
# APM 을 둘 잇는다. 하나는 지금 바이트의 부분 문맥(c0)만 보고, 하나는
# 거기에 **직전 바이트** 를 더해 본다. 작은 파일에서 특히 값을 한다 —
# 표가 아직 차갑고 가중치도 배우는 중일 때 치우침을 빨리 잡아 준다.
APM1_CONTEXTS = 256
APM2_CONTEXTS = 1 << 16
HASH_A = 0x9E3779B1
HASH_B = 0x85EBCA6B
U32 = 0xFFFFFFFF

# SQUASH-TABLE-BEGIN — gen_tables.py 가 다섯 언어를 대조한다 (§18.6)
SQUASH_TABLE = [
    1, 2, 3, 6, 10, 16, 27, 45, 73, 120, 194, 310, 488, 747, 1101,
    1546, 2047, 2549, 2994, 3348, 3607, 3785, 3901, 3975, 4024,
    4050, 4068, 4079, 4085, 4089, 4092, 4093, 4094]
# SQUASH-TABLE-END


def squash(d):
    """로지스틱: -2047..2047 → 0..4095. 표 사이를 직선으로 잇는다."""
    if d > 2047:
        return 4095
    if d < -2047:
        return 0
    w = d & 127
    i = (d >> 7) + 16
    return ((SQUASH_TABLE[i] * (128 - w)
             + SQUASH_TABLE[i + 1] * w + 64) >> 7)


def _make_stretch():
    """squash 의 역. 표를 뒤집어 만든다 — 따로 적을 값이 아니다."""
    table = [0] * PROB_ONE
    pi = 0
    for x in range(-2047, 2048):
        v = squash(x)
        for p in range(pi, v + 1):
            table[p] = x
        pi = v + 1
    for p in range(pi, PROB_ONE):
        table[p] = 2047
    return table


STRETCH_TABLE = _make_stretch()


def stretch(p):
    return STRETCH_TABLE[p]


def _hash(ctx, c0):
    h = ((ctx * HASH_A) & U32) ^ ((c0 * HASH_B) & U32)
    return (h & U32) >> (32 - TABLE_BITS)


class Apm:
    """적응 확률 지도 — 믹서의 답을 문맥에 맞춰 다시 고친다 (§18.5)."""

    def __init__(self, contexts):
        # array 로 담는다. 파이썬 리스트에 정수 216만 개를 넣으면 객체가
        # 그만큼 생겨 70 MB 를 먹는다 — 이 기계에서는 그것도 위험하다.
        self.t = array('i', (squash(((i % 33) - 16) * 128) * 16
                             for i in range(contexts * 33)))
        self.index = 0

    def pp(self, pr, cx):
        # 곱수는 32 다. 표가 33칸이라 0..4095 를 0..32 로 펴야 끝까지
        # 쓴다. lpaq1 의 23 을 그대로 옮기면 위쪽 아홉 칸이 죽어
        # 확률이 3200 쯤에서 잘린다 — 비율이 무너져서 알았다.
        s = (stretch(pr) + 2048) * 32
        wt = s & 0xFFF
        j = cx * 33 + (s >> 12)
        self.index = j + (wt >> 11)
        return (self.t[j] * (4096 - wt) + self.t[j + 1] * wt) >> 16

    def update(self, bit):
        g = (bit << 16) + (bit << APM_RATE) - bit - bit
        self.t[self.index] += (g - self.t[self.index]) >> APM_RATE


class Model:
    """문맥 모델 다섯 + 믹서 + APM. 부호기와 복호기가 똑같이 쓴다."""

    def __init__(self):
        self.order0 = array('H', [PROB_HALF] * 256)
        self.order0_n = bytearray(256)
        # 확률은 부호 없는 16비트, 셈은 바이트. 리스트로 두면 표 하나에
        # 130 MB 가 든다 (§18.3 의 2^20 칸 × 4개).
        self.tables = [array('H', bytes(TABLE_SIZE * 2))
                       for _ in range(4)]
        for t in self.tables:
            for i in range(TABLE_SIZE):
                t[i] = PROB_HALF
        self.counts = [bytearray(TABLE_SIZE) for _ in range(4)]
        self.weights = [array('i', [MIXER_INIT] * NUM_MODELS)
                        for _ in range(256)]
        self.apm1 = Apm(APM1_CONTEXTS)
        self.apm2 = Apm(APM2_CONTEXTS)
        self.history = 0            # 마지막 네 바이트
        self.c0 = 1                 # 지금까지 받은 비트 (1 에서 시작)
        self.slots = [0] * NUM_MODELS
        self.st = [0] * NUM_MODELS
        self.p_mix = PROB_HALF
        self.p_final = PROB_HALF

    def predict(self):
        c0 = self.c0
        h = self.history
        self.slots[0] = c0 & 0xFF
        for k in range(4):
            ctx = h & ((1 << (8 * (k + 1))) - 1)
            self.slots[k + 1] = _hash(ctx + (k + 1) * 0x01000193, c0)
        probs = [self.order0[self.slots[0]]]
        for k in range(4):
            probs.append(self.tables[k][self.slots[k + 1]])
        w = self.weights[c0 & 0xFF]
        dot = 0
        for i in range(NUM_MODELS):
            self.st[i] = stretch(probs[i])
            dot += w[i] * self.st[i]
        dot >>= MIXER_SHIFT
        if dot > 2047:
            dot = 2047
        elif dot < -2047:
            dot = -2047
        self.p_mix = squash(dot)
        p = (self.p_mix + 3 * self.apm1.pp(self.p_mix, c0 & 0xFF)) >> 2
        cx2 = ((c0 & 0xFF) << 8) | (h & 0xFF)
        p = (p + 3 * self.apm2.pp(p, cx2)) >> 2
        if p < 1:
            p = 1
        elif p > 4094:
            p = 4094
        self.p_final = p
        return p

    def update(self, bit):
        target = bit << 12
        i0 = self.slots[0]
        self.order0[i0] += ((target - self.order0[i0])
                            >> COUNTER_RATES[self.order0_n[i0]])
        if self.order0_n[i0] < COUNTER_LIMIT:
            self.order0_n[i0] += 1
        for k in range(4):
            t = self.tables[k]
            c = self.counts[k]
            i = self.slots[k + 1]
            t[i] += (target - t[i]) >> COUNTER_RATES[c[i]]
            if c[i] < COUNTER_LIMIT:
                c[i] += 1
        err = (target - self.p_mix) * MIXER_LEARN
        w = self.weights[self.c0 & 0xFF]
        for i in range(NUM_MODELS):
            v = w[i] + ((self.st[i] * err) >> MIXER_UPDATE_SHIFT)
            if v > MIXER_CLAMP:
                v = MIXER_CLAMP
            elif v < -MIXER_CLAMP:
                v = -MIXER_CLAMP
            w[i] = v
        self.apm1.update(bit)
        self.apm2.update(bit)
        self.c0 = (self.c0 << 1) | bit
        if self.c0 >= 256:
            byte = self.c0 & 0xFF
            self.history = ((self.history << 8) | byte) & U32
            self.c0 = 1


def encode(src):
    if not src:
        return varint.put(0)
    enc = rangecoder.Encoder()
    model = Model()
    probs = [0]
    for b in src:
        for i in range(7, -1, -1):
            bit = (b >> i) & 1
            probs[0] = model.predict()
            # 코더는 P(0) 을 받는다. 모델은 P(1) 을 내므로 뒤집는다.
            enc.encode_bit_p0(PROB_ONE - probs[0], bit)
            model.update(bit)
    enc.flush()
    return varint.put(len(src)) + enc.bytes()


def decode(src):
    n, pos = varint.get_length(src)
    if n == 0:
        if pos != len(src):
            raise ValueError('빈 입력인데 뒤에 바이트가 있다')
        return b''
    dec = rangecoder.Decoder(src, pos)
    model = Model()
    out = bytearray()
    for _ in range(n):
        byte = 0
        for _i in range(8):
            p = model.predict()
            bit = dec.decode_bit_p0(PROB_ONE - p)
            model.update(bit)
            byte = (byte << 1) | bit
        out.append(byte)
    return bytes(out)
