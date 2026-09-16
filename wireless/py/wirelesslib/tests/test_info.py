# -*- coding: utf-8 -*-
"""info 모듈의 증인 시험.

용량은 이 책이 되풀이해 되부르는 잣대다. "이 규격이 섀넌 한계에서
얼마나 떨어져 있나" 를 묻는 모든 장이 여기 값을 쓴다. 그래서 몬테카를로
결과를 반드시 닫힌 식과 맞댄다.

  · AWGN 용량이 0 dB 에서 정확히 1 bit/s/Hz 인가
  · 레일리 에르고딕 용량의 표본 평균이 닫힌 식과 맞는가
    (log₂e · e^{1/ρ} · E₁(1/ρ))
  · 물채우기가 전력을 남김없이 쓰고, 쓰는 채널의 수위가 모두 같은가
  · 2×2 MIMO 가 높은 SNR 에서 SISO 의 두 배 기울기로 늘어나는가
  · 성상도의 상호정보가 높은 SNR 에서 k 비트로 수렴하는가,
    그리고 섀넌 용량을 넘지 않는가
"""
import math
import unittest

from wirelesslib import info


class TestE1(unittest.TestCase):
    def test_known_values(self):
        self.assertAlmostEqual(info.e1(0.5), 0.5597735947, places=9)
        self.assertAlmostEqual(info.e1(1.0), 0.2193839344, places=9)
        self.assertAlmostEqual(info.e1(2.0), 0.0489005107, places=9)
        self.assertAlmostEqual(info.e1(10.0), 4.156968929e-6, places=13)

    def test_monotone_decreasing(self):
        prev = 1e9
        for x in (0.1, 0.5, 1.0, 3.0, 8.0, 20.0):
            v = info.e1(x)
            self.assertLess(v, prev)
            prev = v

    def test_rejects_nonpositive(self):
        with self.assertRaises(ValueError):
            info.e1(0.0)


class TestAwgnCapacity(unittest.TestCase):
    def test_one_bit_at_0db(self):
        self.assertAlmostEqual(info.capacity_awgn(0.0), 1.0, places=12)

    def test_doubling_snr_adds_one_bit_at_high_snr(self):
        """높은 SNR 에서만 참인 점근이다.

        30 dB 에서는 아직 0.999 비트다.
        """
        self.assertAlmostEqual(
            info.capacity_awgn(30.0 + 10 * math.log10(2.0))
            - info.capacity_awgn(30.0), 1.0, places=3 - 1)
        self.assertAlmostEqual(
            info.capacity_awgn(60.0 + 10 * math.log10(2.0))
            - info.capacity_awgn(60.0), 1.0, places=5)

    def test_low_snr_is_linear(self):
        """SNR 이 작으면 C ≈ ρ·log₂e — 전력에 비례한다."""
        # 다음 항이 −ρ²/2·log₂e 이므로 상대 오차는 ρ/2 남짓이다.
        for rho in (1e-4, 1e-6):
            snr_db = 10 * math.log10(rho)
            got = info.capacity_awgn(snr_db)
            want = rho * math.log2(math.e)
            self.assertLess(abs(got - want) / want, rho)

    def test_ebn0_limit(self):
        """스펙트럼 효율을 0 으로 보내면 Eb/N0 가 ln2 로 간다."""
        self.assertAlmostEqual(info.ebn0_min_db(1e-6), -1.5917,
                               places=3)


class TestRayleighCapacity(unittest.TestCase):
    def test_ergodic_closed_form_matches_monte_carlo(self):
        for snr_db in (0.0, 10.0, 20.0):
            exact = info.capacity_rayleigh_ergodic(snr_db)
            mc = info.capacity_rayleigh_mc(snr_db, 40000, seed=20260916)
            self.assertLess(abs(mc - exact) / exact, 0.02,
                            'SNR=%g exact=%g mc=%g'
                            % (snr_db, exact, mc))

    def test_ergodic_is_below_awgn(self):
        """같은 평균 SNR 이면 페이딩이 언제나 손해다 (젠센 부등식)."""
        for snr_db in (0.0, 5.0, 10.0, 20.0):
            self.assertLess(info.capacity_rayleigh_ergodic(snr_db),
                            info.capacity_awgn(snr_db))

    def test_ergodic_at_0db(self):
        self.assertAlmostEqual(info.capacity_rayleigh_ergodic(0.0),
                               0.8603, places=3)

    def test_outage_capacity_matches_empirical_quantile(self):
        snr_db, eps = 10.0, 0.1
        want = info.capacity_rayleigh_outage(snr_db, eps)
        h2 = [abs(v) ** 2 for v in
              __import__('wirelesslib.channel', fromlist=['x'])
              .rayleigh(20000, seed=5)]
        caps = sorted(math.log2(1 + info.db2lin(snr_db) * g)
                      for g in h2)
        emp = caps[int(eps * len(caps))]
        self.assertLess(abs(emp - want) / want, 0.05)

    def test_outage_rises_with_allowed_outage(self):
        prev = 0.0
        for eps in (0.01, 0.05, 0.1, 0.5):
            v = info.capacity_rayleigh_outage(10.0, eps)
            self.assertGreater(v, prev)
            prev = v


class TestWaterfilling(unittest.TestCase):
    def test_uses_all_power(self):
        gains = [4.0, 2.0, 1.0, 0.25]
        p = info.waterfill(gains, 10.0)
        self.assertAlmostEqual(sum(p), 10.0, places=9)

    def test_equal_gains_get_equal_power(self):
        p = info.waterfill([1.0] * 4, 8.0)
        for v in p:
            self.assertAlmostEqual(v, 2.0, places=9)

    def test_water_level_is_flat_where_used(self):
        gains = [8.0, 4.0, 1.0, 0.1]
        p = info.waterfill(gains, 3.0)
        lv = [pi + 1.0 / g for pi, g in zip(p, gains) if pi > 1e-12]
        for v in lv:
            self.assertAlmostEqual(v, lv[0], places=9)

    def test_weak_channel_is_switched_off(self):
        p = info.waterfill([10.0, 0.001], 0.2)
        self.assertAlmostEqual(p[1], 0.0, places=12)
        self.assertAlmostEqual(p[0], 0.2, places=9)

    def test_beats_equal_allocation(self):
        gains = [8.0, 4.0, 1.0, 0.1]
        total = 4.0
        wf = info.capacity_parallel(gains, info.waterfill(gains, total))
        eq = info.capacity_parallel(gains, [total / 4.0] * 4)
        self.assertGreater(wf, eq)


class TestMimo(unittest.TestCase):
    def test_siso_matches_awgn_formula(self):
        h = [[1 + 0j]]
        self.assertAlmostEqual(info.mimo_capacity(h, 10.0),
                               info.capacity_awgn(10.0), places=9)

    def test_identity_channel_is_n_parallel_channels(self):
        """H = I 면 서로 간섭 없는 채널 N 개다 — N·log₂(1+ρ/N)."""
        for n in (2, 4):
            h = [[1.0 + 0j if i == j else 0j for j in range(n)]
                 for i in range(n)]
            want = n * math.log2(1.0 + info.db2lin(15.0) / n)
            self.assertAlmostEqual(info.mimo_capacity(h, 15.0), want,
                                   places=9)

    def test_2x2_doubles_slope_at_high_snr(self):
        """다중화 이득이 2 면 SNR 10 dB 당 약 2 비트가 는다."""
        a = info.mimo_capacity_mc(2, 2, 20.0, 400, seed=3)
        b = info.mimo_capacity_mc(2, 2, 30.0, 400, seed=3)
        self.assertAlmostEqual((b - a) / math.log2(10.0), 2.0,
                               delta=0.25)

    def test_2x2_beats_siso(self):
        s = info.mimo_capacity_mc(1, 1, 20.0, 400, seed=7)
        m = info.mimo_capacity_mc(2, 2, 20.0, 400, seed=7)
        self.assertGreater(m / s, 1.7)
        self.assertLess(m / s, 2.2)

    def test_receive_diversity_gives_array_gain_only(self):
        """1×2 는 흐름이 하나라 기울기는 그대로고 이득만 붙는다."""
        a = info.mimo_capacity_mc(1, 2, 20.0, 400, seed=11)
        b = info.mimo_capacity_mc(1, 2, 30.0, 400, seed=11)
        self.assertAlmostEqual((b - a) / math.log2(10.0), 1.0,
                               delta=0.2)


class TestConstellationMI(unittest.TestCase):
    def test_saturates_at_k_bits(self):
        for name, k in (('qpsk', 2), ('16qam', 4)):
            mi = info.constellation_mi(name, 30.0, 2000, seed=2)
            self.assertAlmostEqual(mi, float(k), delta=0.02)

    def test_never_exceeds_shannon(self):
        for name in ('qpsk', '16qam', '64qam'):
            for snr in (0.0, 5.0, 10.0, 15.0):
                mi = info.constellation_mi(name, snr, 1500, seed=4)
                self.assertLessEqual(mi, info.capacity_awgn(snr) + 0.03,
                                     '%s %g dB' % (name, snr))

    def test_rises_with_snr(self):
        prev = 0.0
        for snr in (0.0, 5.0, 10.0, 15.0):
            v = info.constellation_mi('16qam', snr, 1500, seed=6)
            self.assertGreater(v, prev - 1e-9)
            prev = v


if __name__ == '__main__':
    unittest.main()
