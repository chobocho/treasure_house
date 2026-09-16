# -*- coding: utf-8 -*-
"""channel 모듈의 증인 시험.

무선 채널은 이 책에서 가장 '믿고 넘어가기 쉬운' 자리다. 페이딩 발생기는
그럴듯한 숫자를 내면서도 통계가 틀릴 수 있고, 경로손실식은 상수 하나가
틀려도 그래프 모양이 같다. 그래서 통계와 상수를 따로 붙잡는다.

  · 레일리 포락선의 CDF 가 1 − e^{−r²} 인가
  · 라이시안이 K→0 에서 레일리로 가고, K 가 크면 LOS 성분이 지배하는가
  · 제이크스 발생기의 자기상관이 J₀(2π f_D τ) 인가
  · 레벨 교차율이 √(2π) f_D ρ e^{−ρ²} 인가
  · 자유공간 손실이 1 km·2 GHz 에서 98.5 dB 인가
  · 오쿠무라-하타가 교과서 값과 맞는가
    (900 MHz·기지국 30 m·단말 1.5 m·1 km → 126.4 dB)
"""
import math
import unittest

from wirelesslib import channel


class TestBessel(unittest.TestCase):
    def test_j0_known_values(self):
        self.assertAlmostEqual(channel.j0(0.0), 1.0, places=10)
        self.assertAlmostEqual(channel.j0(1.0), 0.7651976866, places=9)
        self.assertAlmostEqual(channel.j0(2.4048255577), 0.0, places=8)
        self.assertAlmostEqual(channel.j0(5.0), -0.1775967713, places=9)

    def test_j0_is_even(self):
        for x in (0.7, 3.1, 8.2):
            self.assertAlmostEqual(channel.j0(-x), channel.j0(x),
                                   places=12)


class TestPathLoss(unittest.TestCase):
    def test_fspl_reference_point(self):
        """1 km, 2 GHz 에서 98.5 dB — 이 책이 계속 되부르는 기준점."""
        self.assertAlmostEqual(channel.fspl_db(1000.0, 2.0e9), 98.5,
                               delta=0.05)

    def test_fspl_doubles_distance_costs_6db(self):
        a = channel.fspl_db(1000.0, 2.0e9)
        b = channel.fspl_db(2000.0, 2.0e9)
        self.assertAlmostEqual(b - a, 20 * math.log10(2.0), places=9)

    def test_fspl_doubles_frequency_costs_6db(self):
        a = channel.fspl_db(1000.0, 1.0e9)
        b = channel.fspl_db(1000.0, 2.0e9)
        self.assertAlmostEqual(b - a, 20 * math.log10(2.0), places=9)

    def test_hata_textbook_value(self):
        """900 MHz · 기지국 30 m · 단말 1.5 m · 1 km · 대도시."""
        got = channel.hata_db(900.0, 30.0, 1.5, 1.0, 'urban_large')
        self.assertAlmostEqual(got, 126.42, places=1)

    def test_hata_suburban_is_lower_than_urban(self):
        u = channel.hata_db(900.0, 30.0, 1.5, 5.0, 'urban_large')
        s = channel.hata_db(900.0, 30.0, 1.5, 5.0, 'suburban')
        o = channel.hata_db(900.0, 30.0, 1.5, 5.0, 'open')
        self.assertLess(s, u)
        self.assertLess(o, s)

    def test_hata_rejects_out_of_range(self):
        with self.assertRaises(ValueError):
            channel.hata_db(2500.0, 30.0, 1.5, 1.0)

    def test_cost231_is_hata_with_new_constants(self):
        """COST-231 은 하타를 1.5~2 GHz 로 늘린 것이다.

        거리 기울기가 하타와 같아야 한다.
        """
        a = channel.cost231_db(1800.0, 30.0, 1.5, 1.0)
        b = channel.cost231_db(1800.0, 30.0, 1.5, 10.0)
        slope = (b - a) / math.log10(10.0)
        self.assertAlmostEqual(slope, 44.9 - 6.55 * math.log10(30.0),
                               places=6)

    def test_log_distance_matches_fspl_at_reference(self):
        d0, f = 100.0, 2.0e9
        pl = channel.log_distance_db(d0, d0, f, 3.5)
        self.assertAlmostEqual(pl, channel.fspl_db(d0, f), places=9)


class TestTr38901(unittest.TestCase):
    def test_los_is_never_worse_than_nlos(self):
        for scen in ('uma', 'umi'):
            for d in (50.0, 200.0, 1000.0):
                los = channel.tr38901_db(scen, d, 3.5, los=True)
                nlos = channel.tr38901_db(scen, d, 3.5, los=False)
                self.assertLessEqual(los, nlos + 1e-9,
                                     '%s %g m' % (scen, d))

    def test_breakpoint_makes_slope_steeper(self):
        """분기점 앞은 거리 지수 2, 뒤는 4 다 — 기울기가 꺾여야 한다."""
        f = 2.0
        near = (channel.tr38901_db('uma', 60.0, f, True)
                - channel.tr38901_db('uma', 30.0, f, True))
        far = (channel.tr38901_db('uma', 2000.0, f, True)
               - channel.tr38901_db('uma', 1000.0, f, True))
        self.assertGreater(far, near + 3.0)

    def test_unknown_scenario(self):
        with self.assertRaises(ValueError):
            channel.tr38901_db('rma', 100.0, 3.5, True)


class TestFading(unittest.TestCase):
    def test_rayleigh_cdf(self):
        """|h| 의 CDF 는 1 − e^{−r²} 다 (평균 전력 1 일 때)."""
        h = channel.rayleigh(20000, seed=20260916)
        p = sum(abs(v) ** 2 for v in h) / len(h)
        self.assertAlmostEqual(p, 1.0, delta=0.03)
        for r in (0.3, 0.7, 1.0, 1.5, 2.0):
            emp = sum(1 for v in h if abs(v) <= r) / float(len(h))
            want = 1.0 - math.exp(-r * r)
            self.assertLess(abs(emp - want), 0.012, 'r=%g' % r)

    def test_rician_k_zero_is_rayleigh(self):
        a = channel.rician(5000, 0.0, seed=4)
        b = channel.rayleigh(5000, seed=4)
        for x, y in zip(a, b):
            self.assertLess(abs(x - y), 1e-12)

    def test_rician_power_split(self):
        """K 는 직접파와 산란파의 전력비다. 총 전력은 1 로 둔다."""
        for k in (1.0, 5.0, 10.0):
            h = channel.rician(20000, k, seed=11)
            p = sum(abs(v) ** 2 for v in h) / len(h)
            self.assertAlmostEqual(p, 1.0, delta=0.05)
            mean = sum(h) / len(h)
            self.assertAlmostEqual(abs(mean) ** 2, k / (k + 1.0),
                                   delta=0.05)

    def test_jakes_autocorrelation_is_bessel(self):
        """클라크 스펙트럼의 자기상관은 J₀(2π f_D τ) 다."""
        fd, fs, n = 50.0, 2000.0, 30000
        h = channel.jakes(n, fd, fs, seed=7, nsin=32)
        p = sum(abs(v) ** 2 for v in h) / n
        for lag in (0, 4, 8, 16, 24, 40):
            acc = sum((h[i] * h[i + lag].conjugate()).real
                      for i in range(n - lag)) / (n - lag) / p
            want = channel.j0(2 * math.pi * fd * lag / fs)
            self.assertLess(abs(acc - want), 0.06, 'lag=%d' % lag)

    def test_level_crossing_rate(self):
        """LCR = √(2π)·f_D·ρ·e^{−ρ²} — 페이딩의 '빠르기' 를 재는 식."""
        fd, fs, n = 100.0, 4000.0, 80000
        h = channel.jakes(n, fd, fs, seed=3, nsin=32)
        rms = math.sqrt(sum(abs(v) ** 2 for v in h) / n)
        for rho in (0.5, 1.0):
            got = channel.level_crossing_rate(h, rho * rms, fs)
            want = (math.sqrt(2 * math.pi) * fd * rho
                    * math.exp(-rho * rho))
            self.assertLess(abs(got - want) / want, 0.15,
                            'rho=%g got=%g want=%g' % (rho, got, want))


class TestCoherence(unittest.TestCase):
    def test_doppler_shift(self):
        # 시속 120 km, 2 GHz, 정면 → 222 Hz 남짓
        v = 120.0 / 3.6
        self.assertAlmostEqual(channel.doppler_hz(v, 2.0e9), 222.4,
                               places=1)

    def test_coherence_time_from_doppler(self):
        self.assertAlmostEqual(channel.coherence_time_s(100.0),
                               0.423 / 100.0, places=9)

    def test_coherence_bandwidth_from_spread(self):
        self.assertAlmostEqual(channel.coherence_bw_hz(1e-6),
                               1.0 / (5.0 * 1e-6), places=6)

    def test_delay_spread_of_tdl(self):
        """지연 확산은 전력으로 가중한 지연의 표준편차다."""
        taps = [(0.0, 0.5), (1e-6, 0.5)]
        self.assertAlmostEqual(channel.rms_delay_spread(taps), 0.5e-6,
                               places=12)

    def test_tdl_single_tap_is_scaling(self):
        taps = [(0.0, 1.0)]
        x = [1 + 0j, 2 + 0j, 3 + 0j]
        y = channel.tdl_apply(x, taps, 1e6, seed=1, fd=0.0)
        for a, b in zip(x, y):
            self.assertLess(abs(abs(b) - abs(a)), 1e-9)

    def test_tdl_power_is_preserved_on_average(self):
        """탭이 독립이면 받은 전력의 기댓값은 탭 전력의 합이다.

        한 번만 돌려서는 못 본다 — 2 ms 창에서 30 Hz 페이딩은 사실상
        한 표본이라 실현값이 크게 흔들린다. 그래서 씨앗을 바꿔 가며
        여러 번 돌린 평균을 본다.
        """
        taps = [(0.0, 0.6), (5e-7, 0.4)]
        x = [1 + 0j] * 200
        tot = 0.0
        runs = 40
        for s in range(runs):
            y = channel.tdl_apply(x, taps, 2e6, seed=s, fd=30.0)
            tot += sum(abs(v) ** 2 for v in y) / len(y)
        self.assertAlmostEqual(tot / runs, 1.0, delta=0.15)


class TestShadowing(unittest.TestCase):
    def test_lognormal_std(self):
        s = channel.shadowing_db(20000, 8.0, seed=2)
        m = sum(s) / len(s)
        sd = math.sqrt(sum((v - m) ** 2 for v in s) / len(s))
        self.assertLess(abs(m), 0.2)
        self.assertLess(abs(sd - 8.0), 0.2)


if __name__ == '__main__':
    unittest.main()
