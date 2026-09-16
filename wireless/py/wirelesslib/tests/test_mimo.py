# -*- coding: utf-8 -*-
"""mimo 모듈의 증인 시험.

다중 안테나가 벌어 주는 것은 셋이다 — 다이버시티, 다중화, 배열 이득.
셋을 각각 숫자로 붙잡는다.

  · 알라무티가 **다이버시티 차수 2** 를 내는가 (BER 기울기가 −2)
  · ZF·MMSE 가 잡음 없으면 정확히 되돌리는가,
    그리고 낮은 SNR 에서 MMSE 가 나은가
  · 특잇값으로 구한 용량이 log₂det 공식과 같은가
  · N 소자 균일 선형 배열의 최대 배열 이득이 10·log₁₀N 인가
  · 안테나가 늘면 채널이 굳는가 (massive MIMO 의 채널 경화)
"""
import math
import unittest

from wirelesslib import info, mimo


class TestAlamouti(unittest.TestCase):
    def test_noiseless_roundtrip(self):
        rnd = __import__('random').Random(1)
        for _ in range(50):
            s = [complex(1 - 2 * rnd.getrandbits(1),
                         1 - 2 * rnd.getrandbits(1)) for _ in range(2)]
            h = [complex(rnd.gauss(0, 1), rnd.gauss(0, 1))
                 for _ in range(2)]
            y = mimo.alamouti_channel(s, h)
            got = mimo.alamouti_decode(y, h)
            for a, b in zip(s, got):
                self.assertLess(abs(a - b), 1e-9)

    def test_diversity_order_is_two(self):
        """BER 이 SNR 의 −2 제곱으로 떨어져야 한다."""
        lo = mimo.alamouti_ber(14.0, 4000, seed=3)
        hi = mimo.alamouti_ber(20.0, 4000, seed=3)
        slope = math.log10(lo / hi) / ((20.0 - 14.0) / 10.0)
        self.assertGreater(slope, 1.6)
        self.assertLess(slope, 2.4)

    def test_siso_diversity_order_is_one(self):
        lo = mimo.siso_rayleigh_ber(14.0, 20000, seed=5)
        hi = mimo.siso_rayleigh_ber(20.0, 20000, seed=5)
        slope = math.log10(lo / hi) / ((20.0 - 14.0) / 10.0)
        self.assertGreater(slope, 0.7)
        self.assertLess(slope, 1.3)

    def test_alamouti_beats_siso(self):
        a = mimo.alamouti_ber(14.0, 4000, seed=7)
        s = mimo.siso_rayleigh_ber(14.0, 20000, seed=7)
        self.assertLess(a, s)


class TestDetection(unittest.TestCase):
    def test_zf_is_exact_without_noise(self):
        h = [[2 + 0j, 1j], [0.5 + 0j, 1 - 1j]]
        x = [1 + 0j, -1 + 2j]
        y = mimo.apply_channel(h, x)
        got = mimo.zf_detect(h, y)
        for a, b in zip(x, got):
            self.assertLess(abs(a - b), 1e-9)

    def test_mmse_tends_to_zf_at_high_snr(self):
        h = [[2 + 0j, 1j], [0.5 + 0j, 1 - 1j]]
        x = [1 + 0j, -1 + 2j]
        y = mimo.apply_channel(h, x)
        zf = mimo.zf_detect(h, y)
        mm = mimo.mmse_detect(h, y, 1e-12)
        for a, b in zip(zf, mm):
            self.assertLess(abs(a - b), 1e-6)

    def test_mmse_beats_zf_at_low_snr(self):
        z = mimo.detect_mse(0.0, 400, seed=11, kind='zf')
        m = mimo.detect_mse(0.0, 400, seed=11, kind='mmse')
        self.assertLess(m, z)

    def test_singular_matrix_is_reported(self):
        h = [[1 + 0j, 2 + 0j], [2 + 0j, 4 + 0j]]
        with self.assertRaises(ValueError):
            mimo.zf_detect(h, [1 + 0j, 2 + 0j])


class TestSVD(unittest.TestCase):
    def test_singular_values_energy(self):
        """Σσ² 은 행렬의 프로베니우스 노름 제곱과 같다."""
        rnd = __import__('random').Random(13)
        for n in (2, 3, 4):
            h = [[complex(rnd.gauss(0, 1), rnd.gauss(0, 1))
                  for _ in range(n)] for _ in range(n)]
            sv = mimo.singular_values(h)
            fro = sum(abs(v) ** 2 for row in h for v in row)
            self.assertAlmostEqual(sum(s * s for s in sv), fro,
                                   places=8)

    def test_capacity_from_singular_values(self):
        """특잇값으로 센 용량이 log₂det 공식과 같아야 한다."""
        rnd = __import__('random').Random(17)
        for _ in range(10):
            h = [[complex(rnd.gauss(0, 0.7), rnd.gauss(0, 0.7))
                  for _ in range(2)] for _ in range(2)]
            a = info.mimo_capacity(h, 12.0)
            b = mimo.capacity_from_sv(mimo.singular_values(h), 2, 12.0)
            self.assertAlmostEqual(a, b, places=8)

    def test_identity_has_unit_singular_values(self):
        h = [[1 + 0j, 0j], [0j, 1 + 0j]]
        for s in mimo.singular_values(h):
            self.assertAlmostEqual(s, 1.0, places=9)

    def test_rank_one_channel_has_one_stream(self):
        h = [[1 + 0j, 1 + 0j], [1 + 0j, 1 + 0j]]
        sv = mimo.singular_values(h)
        self.assertAlmostEqual(sv[0], 2.0, places=8)
        self.assertLess(sv[1], 1e-8)


class TestArray(unittest.TestCase):
    def test_peak_gain_is_n(self):
        """조향 방향에서 배열 이득은 정확히 N 배 — 10·log₁₀N dB."""
        for n in (2, 4, 8, 64):
            g = mimo.array_gain_db(n)
            self.assertAlmostEqual(g, 10 * math.log10(n), places=9)

    def test_array_factor_peaks_at_steer(self):
        n, steer = 8, math.radians(30.0)
        af = mimo.array_factor(n, 0.5, steer, steer)
        self.assertAlmostEqual(abs(af), float(n), places=9)

    def test_null_count(self):
        """반파장 간격 N 소자 배열은 주엽 옆에 N−1 개의 널을 갖는다."""
        self.assertEqual(mimo.count_nulls(8, 0.5), 7)

    def test_beamwidth_shrinks_with_n(self):
        prev = 10.0
        for n in (4, 8, 16, 64):
            w = mimo.beamwidth_rad(n, 0.5)
            self.assertLess(w, prev)
            prev = w

    def test_grating_lobe_when_spacing_too_wide(self):
        """간격이 반파장을 넘으면 격자엽이 생긴다 — 배열 설계의 상한."""
        self.assertFalse(mimo.has_grating_lobe(0.5))
        self.assertTrue(mimo.has_grating_lobe(1.0))


class TestHardening(unittest.TestCase):
    def test_variance_falls_as_one_over_n(self):
        """안테나가 늘면 채널 이득의 출렁임이 준다 — 채널 경화."""
        a = mimo.hardening_variance(1, 4000, seed=19)
        b = mimo.hardening_variance(16, 4000, seed=19)
        c = mimo.hardening_variance(64, 4000, seed=19)
        self.assertLess(b, a)
        self.assertLess(c, b)
        self.assertAlmostEqual(a / b, 16.0, delta=3.0)

    def test_mean_is_one(self):
        for n in (1, 8, 32):
            m = mimo.hardening_mean(n, 3000, seed=21)
            self.assertAlmostEqual(m, 1.0, delta=0.05)


if __name__ == '__main__':
    unittest.main()
