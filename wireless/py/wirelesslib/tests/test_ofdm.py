# -*- coding: utf-8 -*-
"""ofdm 모듈의 증인 시험.

OFDM 의 약속은 하나다. "부반송파끼리 서로 간섭하지 않는다." 그 약속은
공짜가 아니라 조건부다 — 순환 전치가 지연 확산보다 길어야 하고, 주파수가
정확히 맞아야 한다. 조건이 지켜질 때와 깨질 때를 둘 다 확인한다.

  · CP 가 지연보다 길면 다중경로가 있어도 심볼 간 간섭이 0 인가
  · CP 가 짧으면 실제로 무너지는가
  · 주파수 오차가 있으면 ICI 가 (πε)²/3 만큼 생기는가
  · SC-FDMA 의 PAPR 이 OFDM 보다 낮은가
  · NR 뉴머롤로지의 산술이 규격과 맞는가 (SCS·슬롯 길이·PRB)
"""
import math
import unittest

from wirelesslib import ofdm


class TestRoundtrip(unittest.TestCase):
    def test_no_channel_roundtrip(self):
        rnd = __import__('random').Random(1)
        for nfft in (128, 256, 1024):
            syms = [complex(1 - 2 * rnd.getrandbits(1),
                            1 - 2 * rnd.getrandbits(1))
                    for _ in range(nfft)]
            x = ofdm.modulate(syms, nfft, ncp=16)
            got = ofdm.demodulate(x, nfft, ncp=16)
            for a, b in zip(syms, got):
                self.assertLess(abs(a - b), 1e-9)

    def test_cp_longer_than_delay_kills_isi(self):
        """CP 가 지연보다 길면 다중경로가 한 탭 곱셈으로 줄어든다."""
        err = ofdm.multipath_error(nfft=256, ncp=16,
                                   taps=[(0, 1.0), (5, 0.6),
                                         (12, 0.3)])
        self.assertLess(err, 1e-9)

    def test_cp_shorter_than_delay_breaks(self):
        err = ofdm.multipath_error(nfft=256, ncp=4,
                                   taps=[(0, 1.0), (9, 0.6)])
        self.assertGreater(err, 1e-3)

    def test_cp_overhead(self):
        self.assertAlmostEqual(ofdm.cp_overhead(2048, 144),
                               144.0 / (2048 + 144), places=12)


class TestICI(unittest.TestCase):
    def test_no_offset_no_ici(self):
        self.assertLess(ofdm.ici_power(256, 0.0), 1e-12)

    def test_small_offset_matches_formula(self):
        """작은 주파수 오차의 ICI 전력은 (πε)²/3 에 가깝다."""
        for eps in (0.01, 0.02, 0.05):
            got = ofdm.ici_power(256, eps)
            want = (math.pi * eps) ** 2 / 3.0
            self.assertLess(abs(got - want) / want, 0.05,
                            'eps=%g got=%g want=%g' % (eps, got, want))

    def test_ici_grows_with_offset(self):
        prev = -1.0
        for eps in (0.0, 0.01, 0.05, 0.1):
            v = ofdm.ici_power(256, eps)
            self.assertGreater(v, prev)
            prev = v


class TestPAPR(unittest.TestCase):
    def test_single_tone_papr_is_zero_db(self):
        x = [complex(math.cos(t), math.sin(t)) for t in range(64)]
        self.assertAlmostEqual(ofdm.papr_db(x), 0.0, places=9)

    def test_ofdm_papr_grows_with_subcarriers(self):
        a = ofdm.mean_papr_db(64, trials=60, seed=3)
        b = ofdm.mean_papr_db(1024, trials=60, seed=3)
        self.assertGreater(b, a)

    def test_scfdma_papr_is_lower(self):
        """상향에 SC-FDMA 를 쓴 이유가 이 한 줄이다."""
        o = ofdm.mean_papr_db(256, trials=80, seed=5, scfdma=False)
        s = ofdm.mean_papr_db(256, trials=80, seed=5, scfdma=True)
        self.assertLess(s, o - 1.0)

    def test_ccdf_is_monotone(self):
        c = ofdm.papr_ccdf(256, [4.0, 6.0, 8.0, 10.0], trials=100,
                            seed=7)
        for a, b in zip(c, c[1:]):
            self.assertLessEqual(b, a)


class TestSCFDMA(unittest.TestCase):
    def test_roundtrip(self):
        rnd = __import__('random').Random(9)
        m = 72
        syms = [complex(1 - 2 * rnd.getrandbits(1),
                        1 - 2 * rnd.getrandbits(1)) for _ in range(m)]
        x = ofdm.scfdma_modulate(syms, nfft=1024, ncp=72, offset=120)
        got = ofdm.scfdma_demodulate(x, nfft=1024, ncp=72,
                                     offset=120, m=m)
        for a, b in zip(syms, got):
            self.assertLess(abs(a - b), 1e-8)

    def test_dft_size_must_fit_the_fft(self):
        with self.assertRaises(ValueError):
            ofdm.scfdma_modulate([1 + 0j] * 9, nfft=8, ncp=1,
                                 offset=0)

    def test_lte_dft_sizes_work(self):
        """LTE 의 DFT 크기는 2^a·3^b·5^c — 12의 배수다."""
        rnd = __import__('random').Random(12)
        for m in (12, 24, 36, 72, 180):
            syms = [complex(1 - 2 * rnd.getrandbits(1),
                            1 - 2 * rnd.getrandbits(1))
                    for _ in range(m)]
            x = ofdm.scfdma_modulate(syms, 2048, 144, 300)
            got = ofdm.scfdma_demodulate(x, 2048, 144, 300, m)
            for a, b in zip(syms, got):
                self.assertLess(abs(a - b), 1e-8)


class TestNumerology(unittest.TestCase):
    def test_subcarrier_spacing(self):
        for mu, khz in ((0, 15), (1, 30), (2, 60), (3, 120), (4, 240),
                        (5, 480), (6, 960)):
            self.assertEqual(ofdm.scs_khz(mu), khz)

    def test_slot_length(self):
        """NR 슬롯은 1 ms / 2^μ 다 — 뉴머롤로지의 뼈대."""
        for mu in range(7):
            self.assertAlmostEqual(ofdm.slot_ms(mu),
                                   1.0 / (1 << mu), places=12)

    def test_slots_per_subframe(self):
        for mu in range(7):
            self.assertEqual(ofdm.slots_per_subframe(mu), 1 << mu)

    def test_symbols_per_slot(self):
        self.assertEqual(ofdm.symbols_per_slot('normal'), 14)
        self.assertEqual(ofdm.symbols_per_slot('extended'), 12)

    def test_extended_cp_only_at_60khz(self):
        self.assertTrue(ofdm.extended_cp_allowed(2))
        for mu in (0, 1, 3, 4):
            self.assertFalse(ofdm.extended_cp_allowed(mu))

    def test_prb_is_twelve_subcarriers(self):
        for mu in range(5):
            self.assertAlmostEqual(ofdm.prb_khz(mu),
                                   12 * ofdm.scs_khz(mu), places=9)

    def test_lte_prb_is_180khz(self):
        self.assertAlmostEqual(ofdm.prb_khz(0), 180.0, places=9)

    def test_symbol_duration_times_scs_is_one(self):
        """유용 심볼 길이 × 부반송파 간격 = 1 — 직교 조건 그 자체."""
        for mu in range(5):
            t = ofdm.useful_symbol_us(mu)
            self.assertAlmostEqual(t * ofdm.scs_khz(mu) * 1e-3, 1.0,
                                   places=12)

    def test_rejects_bad_numerology(self):
        with self.assertRaises(ValueError):
            ofdm.scs_khz(7)


if __name__ == '__main__':
    unittest.main()
