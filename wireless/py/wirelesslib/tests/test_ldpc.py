# -*- coding: utf-8 -*-
"""ldpc 모듈의 증인 시험.

LDPC 는 "복호기가 뭔가 하고는 있는데 맞는지 모르겠는" 부호다. 그래서
부호 쪽과 복호 쪽을 따로 붙잡는다.

  · 부호어마다 H·c = 0 인가 (모든 검사식이 실제로 만족되는가)
  · 탄너 그래프에 4-순환이 없는가 — 있으면 믿음 전파가 자기 말을
    되돌려 듣게 되어 성능이 무너진다
  · 잡음이 없으면 한 번 만에 원래 말이 나오는가
  · 오류를 던졌을 때 실제로 고치는가, 그리고 최소합이 합곱보다
    조금 나쁜가 (근사이므로 그래야 한다)
  · 계층 일정이 홍수 일정보다 적은 반복으로 같은 곳에 닿는가
"""
import unittest

from wirelesslib import ldpc


class TestGraph(unittest.TestCase):
    def test_shape(self):
        c = ldpc.NR_LIKE
        h = ldpc.lift(c, 16)
        self.assertEqual(h.n, 24 * 16)
        self.assertEqual(h.m, 14 * 16)
        self.assertEqual(h.k, h.n - h.m)

    def test_no_four_cycles(self):
        """두 검사가 같은 변수 둘을 함께 보면 4-순환이다.

        하나도 없어야 한다.
        """
        h = ldpc.lift(ldpc.NR_LIKE, 16)
        self.assertEqual(ldpc.count_four_cycles(h), 0)

    def test_row_weights_match_base_graph(self):
        h = ldpc.lift(ldpc.NR_LIKE, 8)
        base = ldpc.NR_LIKE
        for r, row in enumerate(base.rows):
            want = len(row)
            for z in range(8):
                self.assertEqual(len(h.rows[r * 8 + z]), want)


class TestEncoder(unittest.TestCase):
    def test_parity_check_is_zero(self):
        rnd = __import__('random').Random(20260916)
        h = ldpc.lift(ldpc.NR_LIKE, 16)
        enc = ldpc.Encoder(h)
        for _ in range(20):
            msg = [rnd.getrandbits(1) for _ in range(h.k)]
            cw = enc.encode(msg)
            self.assertEqual(len(cw), h.n)
            self.assertTrue(ldpc.syndrome_is_zero(h, cw))

    def test_systematic_prefix(self):
        rnd = __import__('random').Random(3)
        h = ldpc.lift(ldpc.NR_LIKE, 8)
        enc = ldpc.Encoder(h)
        msg = [rnd.getrandbits(1) for _ in range(h.k)]
        self.assertEqual(enc.encode(msg)[:h.k], msg)

    def test_all_zero_message_gives_all_zero_codeword(self):
        h = ldpc.lift(ldpc.NR_LIKE, 8)
        enc = ldpc.Encoder(h)
        self.assertEqual(enc.encode([0] * h.k), [0] * h.n)

    def test_linearity(self):
        """선형 부호다 — 두 메시지의 합은 두 부호어의 합이다."""
        rnd = __import__('random').Random(5)
        h = ldpc.lift(ldpc.NR_LIKE, 8)
        enc = ldpc.Encoder(h)
        a = [rnd.getrandbits(1) for _ in range(h.k)]
        b = [rnd.getrandbits(1) for _ in range(h.k)]
        s = [x ^ y for x, y in zip(a, b)]
        ca, cb, cs = enc.encode(a), enc.encode(b), enc.encode(s)
        self.assertEqual(cs, [x ^ y for x, y in zip(ca, cb)])

    def test_rejects_wrong_length(self):
        h = ldpc.lift(ldpc.NR_LIKE, 8)
        with self.assertRaises(ValueError):
            ldpc.Encoder(h).encode([0, 1])


class TestDecoder(unittest.TestCase):
    def setUp(self):
        self.h = ldpc.lift(ldpc.NR_LIKE, 16)
        self.enc = ldpc.Encoder(self.h)

    def test_noiseless_decodes_immediately(self):
        rnd = __import__('random').Random(7)
        msg = [rnd.getrandbits(1) for _ in range(self.h.k)]
        cw = self.enc.encode(msg)
        llr = [(8.0 if b == 0 else -8.0) for b in cw]
        got, it = ldpc.decode(self.h, llr, iters=20)
        self.assertEqual(got, cw)
        self.assertEqual(it, 0)

    def test_corrects_scattered_errors(self):
        rnd = __import__('random').Random(9)
        msg = [rnd.getrandbits(1) for _ in range(self.h.k)]
        cw = self.enc.encode(msg)
        llr = [(4.0 if b == 0 else -4.0) for b in cw]
        for i in (3, 40, 77, 120, 200, 301):
            llr[i] = -llr[i]
        got, it = ldpc.decode(self.h, llr, iters=30)
        self.assertEqual(got, cw)
        self.assertGreater(it, 0)

    def test_min_sum_is_slightly_worse(self):
        """최소합은 근사다 — 같은 잡음에서 합곱보다 나을 수 없다."""
        sp = ldpc.frame_errors(self.h, self.enc, 1.0, 40, iters=20,
                               seed=11, minsum=False)
        ms = ldpc.frame_errors(self.h, self.enc, 1.0, 40, iters=20,
                               seed=11, minsum=True)
        self.assertLessEqual(sp, ms)

    def test_layered_needs_fewer_iterations(self):
        a = ldpc.mean_iters(self.h, self.enc, 2.0, 25, iters=30,
                            seed=13, layered=False)
        b = ldpc.mean_iters(self.h, self.enc, 2.0, 25, iters=30,
                            seed=13, layered=True)
        self.assertLess(b, a)

    def test_more_snr_fewer_frame_errors(self):
        lo = ldpc.frame_errors(self.h, self.enc, 0.0, 40, iters=20,
                               seed=17)
        hi = ldpc.frame_errors(self.h, self.enc, 3.0, 40, iters=20,
                               seed=17)
        self.assertLess(hi, lo)


if __name__ == '__main__':
    unittest.main()
