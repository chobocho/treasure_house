# -*- coding: utf-8 -*-
"""polar 모듈의 증인 시험.

폴라 부호는 "용량을 증명으로 달성한" 첫 구성적 부호다. 그 증명의
알맹이가 극화(polarization) 이므로, 시험도 거기서 시작한다.

  · 극화가 용량을 보존하는가 — 쪼갠 채널들의 용량 합이 N·I(W) 인가
  · 좋은 쪽은 더 좋아지고 나쁜 쪽은 더 나빠지는가 (I⁺ ≥ I ≥ I⁻)
  · 부호화가 선형이고 F^{⊗n} 변환과 맞는가
  · 동결 비트가 0 이면 SC 복호가 잡음 없이 원래 말을 되찾는가
  · 목록 복호(SCL)가 SC 보다 나쁘지 않은가, CRC 를 붙이면 더 나은가
"""
import unittest

from wirelesslib import polar


class TestPolarization(unittest.TestCase):
    def test_capacity_is_conserved(self):
        """쪼갠 채널의 용량 합은 언제나 N·I(W) 다 — 극화의 핵심."""
        for n in (2, 4, 8, 64, 256):
            for i0 in (0.1, 0.5, 0.9):
                caps = polar.capacities(n, i0)
                self.assertEqual(len(caps), n)
                self.assertAlmostEqual(sum(caps), n * i0, places=9)

    def test_polarization_separates(self):
        """N 이 커지면 0 이나 1 에 가까운 채널의 비율이 늘어난다."""
        def extreme(n):
            caps = polar.capacities(n, 0.5)
            return sum(1 for c in caps if c < 0.1 or c > 0.9) / float(n)
        self.assertLess(extreme(4), extreme(64))
        self.assertLess(extreme(64), extreme(1024))

    def test_bhattacharyya_matches_capacity_for_bec(self):
        """BEC 에서는 Z = 소실 확률 = 1 − I 다."""
        for n in (8, 64):
            z = polar.bhattacharyya(n, 0.5)
            caps = polar.capacities(n, 0.5)
            for a, b in zip(z, caps):
                self.assertAlmostEqual(a, 1.0 - b, places=9)

    def test_each_split_is_ordered(self):
        for n in (2, 4, 8):
            caps = polar.capacities(n, 0.5)
            for i in range(0, n, 2):
                self.assertLessEqual(caps[i], caps[i + 1])

    def test_rejects_non_power_of_two(self):
        with self.assertRaises(ValueError):
            polar.capacities(6, 0.5)


class TestTransform(unittest.TestCase):
    def test_transform_matches_kronecker(self):
        """F^{⊗n} 을 직접 만들어 곱한 것과 나비 연산이 같아야 한다."""
        for n in (2, 4, 8, 16):
            g = polar.kronecker_generator(n)
            for v in range(min(1 << n, 64)):
                u = [(v >> i) & 1 for i in range(n)]
                want = [0] * n
                for i in range(n):
                    s = 0
                    for j in range(n):
                        s ^= u[j] & g[j][i]
                    want[i] = s
                self.assertEqual(polar.transform(u), want)

    def test_transform_is_an_involution(self):
        u = [1, 0, 1, 1, 0, 0, 1, 0]
        self.assertEqual(polar.transform(polar.transform(u)), u)

    def test_transform_is_linear(self):
        a = [1, 0, 1, 1]
        b = [0, 1, 1, 0]
        s = [x ^ y for x, y in zip(a, b)]
        ta, tb, ts = (polar.transform(a), polar.transform(b),
                      polar.transform(s))
        self.assertEqual(ts, [x ^ y for x, y in zip(ta, tb)])


class TestConstruction(unittest.TestCase):
    def test_frozen_count(self):
        for n, k in ((8, 4), (64, 32), (256, 100)):
            fz = polar.frozen_set(n, k, 0.5)
            self.assertEqual(len(fz), n - k)

    def test_frozen_are_the_worst_channels(self):
        n, k = 64, 32
        z = polar.bhattacharyya(n, 0.5)
        fz = polar.frozen_set(n, k, 0.5)
        worst = max(z[i] for i in range(n) if i not in fz)
        best_frozen = min(z[i] for i in fz)
        self.assertLessEqual(worst, best_frozen)

    def test_rate_must_fit(self):
        with self.assertRaises(ValueError):
            polar.frozen_set(8, 9, 0.5)


class TestDecoding(unittest.TestCase):
    def test_sc_recovers_noiseless(self):
        rnd = __import__('random').Random(20260916)
        n, k = 64, 32
        fz = polar.frozen_set(n, k, 0.3)
        for _ in range(10):
            msg = [rnd.getrandbits(1) for _ in range(k)]
            x = polar.encode(msg, n, fz)
            llr = [(6.0 if b == 0 else -6.0) for b in x]
            self.assertEqual(polar.sc_decode(llr, n, fz), msg)

    def test_scl_recovers_noiseless(self):
        rnd = __import__('random').Random(3)
        n, k = 64, 32
        fz = polar.frozen_set(n, k, 0.3)
        msg = [rnd.getrandbits(1) for _ in range(k)]
        x = polar.encode(msg, n, fz)
        llr = [(6.0 if b == 0 else -6.0) for b in x]
        self.assertEqual(polar.scl_decode(llr, n, fz, 8), msg)

    def test_scl_is_not_worse_than_sc(self):
        """목록에 SC 의 경로가 언제나 들어 있으므로 나쁠 수 없다."""
        for ebn0 in (1.0, 2.0, 3.0):
            sc = polar.bler(64, 32, ebn0, 40, listsize=1, seed=7)
            scl = polar.bler(64, 32, ebn0, 40, listsize=8, seed=7)
            self.assertLessEqual(scl, sc, 'Eb/N0=%g' % ebn0)

    def test_crc_aided_beats_plain_list(self):
        """CRC 가 목록에서 옳은 경로를 골라 준다 — 그래서 더 낫다."""
        plain = polar.bler(128, 64, 1.5, 40, listsize=8, seed=11)
        aided = polar.bler(128, 64, 1.5, 40, listsize=8, seed=11,
                           crc_name='crc8')
        self.assertLessEqual(aided, plain)

    def test_bler_falls_with_snr(self):
        prev = 1.1
        for ebn0 in (0.0, 2.0, 4.0):
            v = polar.bler(64, 32, ebn0, 30, listsize=4, seed=5)
            self.assertLessEqual(v, prev)
            prev = v


if __name__ == '__main__':
    unittest.main()
