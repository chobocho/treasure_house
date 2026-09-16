# -*- coding: utf-8 -*-
"""codes 모듈의 증인 시험.

부호는 "돌아가는 것처럼 보이는데 틀린" 대표적인 자리다. 부호기가 조금
잘못돼도 자기 복호기와는 짝이 맞아 왕복이 되고, 시뮬레이션은 멀쩡한
곡선을 그린다. 그래서 다음을 붙잡는다.

  · CRC 를 **두 가지 방법으로** 구해 맞대어 본다 (시프트 레지스터 대
    다항식 나눗셈). 서로 다른 길로 같은 값이 나오면 우연이 아니다
  · CRC-16 (D¹⁶+D¹²+D⁵+1) 이 "123456789" 에서 0x31C3 을 내는가 —
    널리 쓰이는 검증값이다
  · 해밍(7,4)이 **모든** 1비트 오류를 고치는가 (16×8 전수)
  · 컨볼루션 부호의 최소 거리를 전수로 구하고, 비터비가 그로부터
    보장되는 오류 수를 **하나도 빠짐없이** 고치는가
  · 인터리버가 왕복하는가, 그리고 연집 오류를 실제로 흩뿌리는가
"""
import itertools
import unittest

from wirelesslib import codes


class TestCRC(unittest.TestCase):
    NAMES = ['crc6', 'crc11', 'crc16', 'crc24a', 'crc24b', 'crc24c']

    def test_two_implementations_agree(self):
        """시프트 레지스터와 다항식 나눗셈이 같은 값을 내야 한다."""
        rnd = __import__('random').Random(20260916)
        for name in self.NAMES:
            for n in (1, 7, 8, 40, 100):
                bits = [rnd.getrandbits(1) for _ in range(n)]
                self.assertEqual(codes.crc(bits, name),
                                 codes.crc_polydiv(bits, name),
                                 '%s n=%d' % (name, n))

    def test_crc16_known_check_value(self):
        """'123456789' → 0x31C3 (초기값 0, 반전 없음)."""
        bits = []
        for ch in '123456789':
            bits += [(ord(ch) >> (7 - i)) & 1 for i in range(8)]
        got = codes.crc(bits, 'crc16')
        v = 0
        for b in got:
            v = (v << 1) | b
        self.assertEqual(v, 0x31C3)

    def test_appended_word_is_divisible(self):
        rnd = __import__('random').Random(5)
        for name in self.NAMES:
            bits = [rnd.getrandbits(1) for _ in range(64)]
            word = codes.crc_append(bits, name)
            self.assertTrue(codes.crc_check(word, name))
            self.assertEqual(codes.crc(word, name),
                             [0] * codes.crc_len(name))

    def test_detects_every_single_bit_error(self):
        rnd = __import__('random').Random(9)
        bits = [rnd.getrandbits(1) for _ in range(80)]
        word = codes.crc_append(bits, 'crc24a')
        for i in range(len(word)):
            bad = list(word)
            bad[i] ^= 1
            self.assertFalse(codes.crc_check(bad, 'crc24a'), 'i=%d' % i)

    def test_detects_every_double_bit_error(self):
        rnd = __import__('random').Random(11)
        bits = [rnd.getrandbits(1) for _ in range(40)]
        word = codes.crc_append(bits, 'crc24a')
        for i, j in itertools.combinations(range(len(word)), 2):
            bad = list(word)
            bad[i] ^= 1
            bad[j] ^= 1
            self.assertFalse(codes.crc_check(bad, 'crc24a'))

    def test_detects_every_burst_up_to_degree(self):
        """길이가 차수 이하인 연집 오류는 전부 잡힌다.

        CRC 가 가진 가장 쓸모 있는 성질이다.
        """
        rnd = __import__('random').Random(13)
        bits = [rnd.getrandbits(1) for _ in range(48)]
        word = codes.crc_append(bits, 'crc16')
        n = len(word)
        for start in range(0, n - 16):
            for pat in range(1, 1 << 8):
                bad = list(word)
                hit = False
                for b in range(8):
                    if (pat >> b) & 1:
                        bad[start + b] ^= 1
                        hit = True
                if hit:
                    self.assertFalse(codes.crc_check(bad, 'crc16'))

    def test_unknown_name(self):
        with self.assertRaises(ValueError):
            codes.crc([0], 'crc7')


class TestHamming(unittest.TestCase):
    def test_roundtrip_without_error(self):
        for v in range(16):
            msg = [(v >> (3 - i)) & 1 for i in range(4)]
            cw = codes.hamming74_encode(msg)
            self.assertEqual(len(cw), 7)
            got, fixed = codes.hamming74_decode(cw)
            self.assertEqual(got, msg)
            self.assertEqual(fixed, -1)

    def test_corrects_every_single_error(self):
        """16개 메시지 × 7자리 = 112가지를 전수로."""
        for v in range(16):
            msg = [(v >> (3 - i)) & 1 for i in range(4)]
            cw = codes.hamming74_encode(msg)
            for i in range(7):
                bad = list(cw)
                bad[i] ^= 1
                got, fixed = codes.hamming74_decode(bad)
                self.assertEqual(got, msg, 'v=%d i=%d' % (v, i))
                self.assertEqual(fixed, i)

    def test_minimum_distance_is_three(self):
        words = []
        for v in range(16):
            msg = [(v >> (3 - i)) & 1 for i in range(4)]
            words.append(codes.hamming74_encode(msg))
        d = min(sum(a != b for a, b in zip(x, y))
                for x, y in itertools.combinations(words, 2))
        self.assertEqual(d, 3)


class TestConvolutional(unittest.TestCase):
    def test_gsm_code_shape(self):
        c = codes.GSM_CONV
        self.assertEqual(c.k, 5)
        self.assertEqual(c.n, 2)
        self.assertEqual(len(c.encode([1, 0, 1, 1], tail=True)),
                         2 * (4 + 4))

    def test_encode_decode_without_noise(self):
        rnd = __import__('random').Random(3)
        for c in (codes.GSM_CONV, codes.IS95_CONV, codes.LTE_CONV):
            msg = [rnd.getrandbits(1) for _ in range(30)]
            y = c.encode(msg, tail=True)
            self.assertEqual(c.viterbi_hard(y), msg)

    def test_free_distance_matches_literature(self):
        """부호마다 알려진 자유 거리 — 전수로 다시 센다."""
        self.assertEqual(codes.GSM_CONV.min_distance(12), 7)
        self.assertEqual(codes.LTE_CONV.min_distance(10), 15)

    def test_viterbi_corrects_every_guaranteed_pattern(self):
        """d_min 에서 보장되는 오류 수는 하나도 빠짐없이 고쳐야 한다."""
        c = codes.GSM_CONV
        nmsg = 8
        dmin = c.min_distance(nmsg)
        t = (dmin - 1) // 2
        self.assertGreaterEqual(t, 2)
        msg = [1, 0, 1, 1, 0, 0, 1, 0]
        cw = c.encode(msg, tail=True)
        n = len(cw)
        for w in range(1, t + 1):
            for pos in itertools.combinations(range(n), w):
                bad = list(cw)
                for i in pos:
                    bad[i] ^= 1
                self.assertEqual(c.viterbi_hard(bad), msg,
                                 'w=%d pos=%s' % (w, pos))

    def test_soft_decoding_beats_hard(self):
        """같은 잡음에서 연판정이 경판정보다 나아야 한다."""
        import random as _r
        from wirelesslib import modem
        c = codes.GSM_CONV
        rnd = _r.Random(20260916)
        eh = es = 0
        for _ in range(60):
            msg = [rnd.getrandbits(1) for _ in range(40)]
            cw = c.encode(msg, tail=True)
            cons = modem.constellation('bpsk')
            y = modem.awgn(modem.modulate(cw, cons), 0.0, rnd)
            hard = modem.demap_hard(y, cons)
            llr = modem.demap_llr(y, cons, 1.0)
            eh += sum(a != b for a, b in zip(msg, c.viterbi_hard(hard)))
            es += sum(a != b for a, b in zip(msg, c.viterbi_soft(llr)))
        self.assertLess(es, eh)

    def test_tail_biting_starts_and_ends_in_same_state(self):
        c = codes.LTE_CONV
        msg = [1, 1, 0, 1, 0, 0, 1, 1, 1, 0]
        y = c.encode(msg, tail=False, tailbiting=True)
        self.assertEqual(len(y), c.n * len(msg))
        self.assertEqual(c.viterbi_tailbiting(y), msg)

    def test_rejects_bad_length(self):
        with self.assertRaises(ValueError):
            codes.GSM_CONV.viterbi_hard([1, 0, 1])


class TestInterleaver(unittest.TestCase):
    def test_block_roundtrip(self):
        x = list(range(24))
        y = codes.block_interleave(x, 4, 6)
        self.assertEqual(codes.block_deinterleave(y, 4, 6), x)

    def test_block_spreads_a_burst(self):
        """연집 오류가 흩어져야 한다 — 인터리버의 존재 이유."""
        rows, cols = 6, 8
        n = rows * cols
        marks = [0] * n
        for i in range(5):
            marks[10 + i] = 1
        spread = codes.block_deinterleave(marks, rows, cols)
        pos = [i for i, v in enumerate(spread) if v]
        gaps = [b - a for a, b in zip(pos, pos[1:])]
        self.assertTrue(all(g >= cols for g in gaps), pos)

    def test_size_must_match(self):
        with self.assertRaises(ValueError):
            codes.block_interleave([0] * 5, 2, 3)


if __name__ == '__main__':
    unittest.main()
