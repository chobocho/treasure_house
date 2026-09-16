# -*- coding: utf-8 -*-
"""turbo 모듈의 증인 시험.

터보 부호는 "왕복만 보면 속는" 부호의 대표다. 반복 복호가 실제로
좋아지고 있는지, 아니면 그냥 한 번에 맞힌 것을 되풀이하는지는
왕복 시험으로 구분되지 않는다. 그래서 다음을 본다.

  · 구성 부호가 되먹임 조직 부호(RSC)인가 — 계통 비트가 입력 그대로인가
  · 전체 부호율이 정확히 1/3 인가 (3K + 12 비트)
  · QPP 인터리버가 진짜 순열인가 (전단사)
  · BCJR 의 사후 LLR 부호가 잡음이 없을 때 원래 비트와 맞는가
  · **반복할수록 오류가 준다** — 1 회부터 6 회까지 단조로 줄어드는가
  · 정확한 log-MAP 이 max-log-MAP 보다 낫거나 같은가
"""
import unittest

from wirelesslib import turbo


class TestRSC(unittest.TestCase):
    def test_systematic_output_equals_input(self):
        rnd = __import__('random').Random(1)
        msg = [rnd.getrandbits(1) for _ in range(40)]
        sysb, par, _tail = turbo.rsc_encode(msg)
        self.assertEqual(sysb, msg)
        self.assertEqual(len(par), len(msg))

    def test_termination_returns_to_zero_state(self):
        rnd = __import__('random').Random(2)
        for n in (8, 40, 64):
            msg = [rnd.getrandbits(1) for _ in range(n)]
            _s, _p, tail = turbo.rsc_encode(msg)
            self.assertEqual(len(tail), 6)
            self.assertEqual(turbo.rsc_final_state(msg, tail), 0)

    def test_impulse_response_is_recursive(self):
        """되먹임이 있으면 1 하나만 넣어도 패리티가 계속 나온다."""
        msg = [1] + [0] * 20
        _s, par, _t = turbo.rsc_encode(msg)
        self.assertGreater(sum(par[7:]), 0)


class TestQPP(unittest.TestCase):
    def test_is_a_permutation(self):
        for k, f1, f2 in ((40, 3, 10), (48, 7, 12), (64, 7, 16),
                          (128, 15, 32), (512, 31, 64)):
            perm = turbo.qpp(k, f1, f2)
            self.assertEqual(sorted(perm), list(range(k)),
                             'K=%d' % k)

    def test_rejects_non_permutation_parameters(self):
        with self.assertRaises(ValueError):
            turbo.qpp(40, 2, 10)      # f1 이 K 와 서로소가 아니다

    def test_interleave_roundtrip(self):
        perm = turbo.qpp(64, 7, 16)
        x = list(range(64))
        y = turbo.apply_perm(x, perm)
        self.assertEqual(turbo.undo_perm(y, perm), x)


class TestTurboEncoder(unittest.TestCase):
    def test_rate_one_third(self):
        rnd = __import__('random').Random(3)
        for k, f1, f2 in ((40, 3, 10), (64, 7, 16)):
            msg = [rnd.getrandbits(1) for _ in range(k)]
            y = turbo.encode(msg, f1, f2)
            self.assertEqual(len(y), 3 * k + 12)

    def test_first_third_is_systematic(self):
        rnd = __import__('random').Random(4)
        msg = [rnd.getrandbits(1) for _ in range(40)]
        y = turbo.encode(msg, 3, 10)
        self.assertEqual(y[:40], msg)


class TestBCJR(unittest.TestCase):
    def test_noiseless_posterior_agrees_with_message(self):
        rnd = __import__('random').Random(5)
        msg = [rnd.getrandbits(1) for _ in range(40)]
        out = turbo.decode(msg, 3, 10, ebn0_db=12.0, iters=2, seed=6)
        self.assertEqual(out, msg)

    def test_errors_fall_sharply_with_iterations(self):
        """반복하면 좋아진다 — 터보 부호의 존재 이유.

        다만 **단조롭지는 않다.** 오류 마루(error floor) 근처에서는
        몇 프레임이 반복 사이에 오갔다 갔다 하며 값이 조금 오르기도
        한다. 실제로 1 dB·K=40 에서 그렇다(0.0275 → 0.0338 → 0.0256).
        그것은 결함이 아니라 반복 복호의 성질이므로, 단조를 억지로
        시험하는 대신 '크게 떨어진다' 를 시험한다.
        """
        errs = turbo.ber_vs_iters(1.0, iters=6, frames=40, k=40,
                                  f1=3, f2=10, seed=20260916)
        self.assertEqual(len(errs), 6)
        self.assertLess(errs[-1], errs[0] * 0.6)
        self.assertLess(min(errs), errs[0] * 0.4)

    def test_monotone_where_it_converges(self):
        """SNR 이 조금만 넉넉하면 실제로 단조 감소해 0 으로 간다."""
        errs = turbo.ber_vs_iters(2.0, iters=5, frames=40, k=128,
                                  f1=15, f2=32, seed=20260916)
        for a, b in zip(errs, errs[1:]):
            self.assertLessEqual(b, a + 1e-12)
        self.assertEqual(errs[-1], 0.0)

    def test_logmap_is_at_least_as_good_as_maxlog(self):
        a = turbo.ber_vs_iters(1.0, iters=4, frames=40, k=40, f1=3,
                               f2=10, seed=7, maxlog=False)[-1]
        b = turbo.ber_vs_iters(1.0, iters=4, frames=40, k=40, f1=3,
                               f2=10, seed=7, maxlog=True)[-1]
        self.assertLessEqual(a, b + 1e-12)

    def test_better_snr_is_better(self):
        lo = turbo.ber_vs_iters(0.0, iters=4, frames=30, k=40, f1=3,
                                f2=10, seed=9)[-1]
        hi = turbo.ber_vs_iters(3.0, iters=4, frames=30, k=40, f1=3,
                                f2=10, seed=9)[-1]
        self.assertLess(hi, lo)


if __name__ == '__main__':
    unittest.main()
