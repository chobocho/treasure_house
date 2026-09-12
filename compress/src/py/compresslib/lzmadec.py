# -*- coding: utf-8 -*-
"""LZMA1 복호기 — SPEC §16.

§8 의 레인지 코더를 LZMA 것으로 쓴 이유가 이 파일이다. 같은 코더에
LZMA 의 문맥 모델만 얹으면 **진짜 xz 가 만든 파일** 이 풀린다.

읽는 것은 LZMA1 "alone" 형식 — `xz --format=lzma` 와 파이썬의
lzma.FORMAT_ALONE 이 쓰는 것이다. .xz 컨테이너는 다른 틀이고 12부에서
말로만 다룬다. "LZMA 를 푼다" 와 ".xz 를 푼다" 는 다른 주장이다.

LZMA 가 DEFLATE 를 이기는 이유는 크게 둘이다.
  · **마지막 거리 넷(rep0..rep3)** 을 기억한다. 되풀이되는 구조는 거리를
    다시 적지 않고 몇 비트로 가리킨다.
  · **일치 뒤의 리터럴** 을 앞 일치의 같은 자리 바이트에 견주어 적는다.
    네 줄짜리 수법인데 텍스트에서 가장 크게 남는다 (§16.6).

부호기는 안 만든다 — bzip2dec 과 같은 이유다 (PLAN.md §0.4).
시간·공간 모두 O(푼 길이).
"""
from compresslib import rangecoder

NUM_STATES = 12
NUM_POS_BITS_MAX = 4
NUM_LEN_TO_POS_STATES = 4
NUM_ALIGN_BITS = 4
END_POS_MODEL_INDEX = 14
NUM_FULL_DISTANCES = 1 << (END_POS_MODEL_INDEX >> 1)
MATCH_MIN_LEN = 2
UNKNOWN_SIZE = 0xFFFFFFFFFFFFFFFF
END_MARKER = 0xFFFFFFFF
PROB_INIT = rangecoder.PROB_INIT
# 손상된 헤더가 불가능한 할당을 요구하지 못하게 (SPEC §12.1)
MAX_OUTPUT = 1 << 32


def _bit_tree(dec, probs, offset, num_bits):
    """위에서부터 내려가는 이진 트리. 결과는 num_bits 짜리 값."""
    m = 1
    for _ in range(num_bits):
        m = (m << 1) + dec.decode_bit(probs, offset + m)
    return m - (1 << num_bits)


def _bit_tree_reverse(dec, probs, offset, num_bits):
    """같은 트리인데 비트를 **거꾸로** 모은다 — 거리의 아래쪽이다."""
    m = 1
    sym = 0
    for i in range(num_bits):
        bit = dec.decode_bit(probs, offset + m)
        m = (m << 1) + bit
        sym |= bit << i
    return sym


class LengthCoder:
    """길이 복호기. 2..273 을 세 구간(8+8+256)으로 나눠 적는다."""

    def __init__(self, pos_states):
        self.choice = [PROB_INIT, PROB_INIT]
        self.low = [PROB_INIT] * (pos_states * 8)
        self.mid = [PROB_INIT] * (pos_states * 8)
        self.high = [PROB_INIT] * 256

    def decode(self, dec, pos_state):
        if dec.decode_bit(self.choice, 0) == 0:
            return _bit_tree(dec, self.low, pos_state * 8, 3)
        if dec.decode_bit(self.choice, 1) == 0:
            return 8 + _bit_tree(dec, self.mid, pos_state * 8, 3)
        return 16 + _bit_tree(dec, self.high, 0, 8)


def parse_header(src):
    """(lc, lp, pb, 사전 크기, 원본 길이, 다음 위치)."""
    if len(src) < 13:
        raise ValueError('LZMA 머리가 너무 짧다')
    prop = src[0]
    if prop >= 9 * 5 * 5:
        raise ValueError('속성 바이트가 범위를 넘는다: %d' % prop)
    lc = prop % 9
    rest = prop // 9
    lp = rest % 5
    pb = rest // 5
    dict_size = int.from_bytes(src[1:5], 'little')
    size = int.from_bytes(src[5:13], 'little')
    if size != UNKNOWN_SIZE and size > MAX_OUTPUT:
        raise ValueError('원본 길이가 너무 크다')
    return lc, lp, pb, dict_size, size, 13


def decode(src):
    lc, lp, pb, _dict_size, want, pos = parse_header(src)
    dec = rangecoder.Decoder(src, pos)
    pos_states = 1 << pb
    pos_mask = pos_states - 1
    lp_mask = (1 << lp) - 1

    is_match = [PROB_INIT] * (NUM_STATES << NUM_POS_BITS_MAX)
    is_rep = [PROB_INIT] * NUM_STATES
    is_rep_g0 = [PROB_INIT] * NUM_STATES
    is_rep_g1 = [PROB_INIT] * NUM_STATES
    is_rep_g2 = [PROB_INIT] * NUM_STATES
    is_rep0_long = [PROB_INIT] * (NUM_STATES << NUM_POS_BITS_MAX)
    pos_slot = [PROB_INIT] * (NUM_LEN_TO_POS_STATES * 64)
    spec_pos = [PROB_INIT] * (NUM_FULL_DISTANCES
                              - END_POS_MODEL_INDEX + 1)
    align_probs = [PROB_INIT] * (1 << NUM_ALIGN_BITS)
    literal = [PROB_INIT] * (0x300 << (lc + lp))
    len_coder = LengthCoder(pos_states)
    rep_len_coder = LengthCoder(pos_states)

    out = bytearray()
    state = 0
    rep0 = rep1 = rep2 = rep3 = 0

    while want == UNKNOWN_SIZE or len(out) < want:
        pos_state = len(out) & pos_mask
        midx = (state << NUM_POS_BITS_MAX) + pos_state
        if dec.decode_bit(is_match, midx) == 0:
            prev = out[-1] if out else 0
            lit_state = (((len(out) & lp_mask) << lc)
                         + (prev >> (8 - lc)))
            base = 0x300 * lit_state
            symbol = 1
            if state >= 7:
                # 일치 뒤의 리터럴 — 앞 일치의 같은 자리 바이트에 견준다
                match_byte = out[len(out) - rep0 - 1]
                while symbol < 0x100:
                    match_bit = (match_byte >> 7) & 1
                    match_byte = (match_byte << 1) & 0xFF
                    bit = dec.decode_bit(
                        literal, base + ((1 + match_bit) << 8) + symbol)
                    symbol = (symbol << 1) | bit
                    if match_bit != bit:
                        break
            while symbol < 0x100:
                symbol = ((symbol << 1)
                          | dec.decode_bit(literal, base + symbol))
            out.append(symbol & 0xFF)
            state = (0 if state < 4
                     else (state - 3 if state < 10 else state - 6))
            continue

        if dec.decode_bit(is_rep, state):
            # 지난 거리 넷 가운데 하나를 다시 쓴다 (§16.4)
            if not out:
                raise ValueError('첫 기호가 되풀이 일치다')
            if dec.decode_bit(is_rep_g0, state) == 0:
                if dec.decode_bit(is_rep0_long, midx) == 0:
                    state = 9 if state < 7 else 11
                    out.append(out[len(out) - rep0 - 1])
                    continue
            else:
                if dec.decode_bit(is_rep_g1, state) == 0:
                    dist = rep1
                else:
                    if dec.decode_bit(is_rep_g2, state) == 0:
                        dist = rep2
                    else:
                        dist = rep3
                        rep3 = rep2
                    rep2 = rep1
                rep1 = rep0
                rep0 = dist
            length = (rep_len_coder.decode(dec, pos_state)
                      + MATCH_MIN_LEN)
            state = 8 if state < 7 else 11
        else:
            rep3, rep2, rep1 = rep2, rep1, rep0
            length = len_coder.decode(dec, pos_state) + MATCH_MIN_LEN
            state = 7 if state < 7 else 10
            slot_state = min(length - MATCH_MIN_LEN,
                             NUM_LEN_TO_POS_STATES - 1)
            slot = _bit_tree(dec, pos_slot, slot_state * 64, 6)
            if slot < 4:
                rep0 = slot
            else:
                direct = (slot >> 1) - 1
                rep0 = (2 | (slot & 1)) << direct
                if slot < END_POS_MODEL_INDEX:
                    rep0 += _bit_tree_reverse(
                        dec, spec_pos, rep0 - slot, direct)
                else:
                    rep0 += dec.decode_direct_bits(
                        direct - NUM_ALIGN_BITS) << NUM_ALIGN_BITS
                    rep0 += _bit_tree_reverse(
                        dec, align_probs, 0, NUM_ALIGN_BITS)
                if rep0 == END_MARKER:
                    break

        # 거리 검사는 한 곳에서만 한다 — 새 일치든 되풀이 일치든 같다.
        if rep0 >= len(out):
            raise ValueError('거리가 지금까지 낸 것보다 멀다')
        start = len(out) - rep0 - 1
        # 한 바이트씩 앞으로. 거리 1 짜리 긴 일치가 여기 기댄다.
        for j in range(length):
            out.append(out[start + j])
        if len(out) > MAX_OUTPUT:
            raise ValueError('푼 길이가 상한을 넘는다')

    if want != UNKNOWN_SIZE and len(out) != want:
        raise ValueError('푼 길이가 머리와 다르다: %d != %d'
                         % (len(out), want))
    return bytes(out)
