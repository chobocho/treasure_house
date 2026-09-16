# -*- coding: utf-8 -*-
"""dsp 모듈의 증인 시험.

이 덱의 규칙은 "숫자를 내는 식에는 그 식을 확인하는 시험이 있다" 이다.
여기서 확인하는 것은 둘이다.

  · FFT 가 정의 그대로의 DFT 와 1e-9 안에서 같은가 —
    빠른 것이 맞기도 한가
  · RRC 두 개를 이어 붙이면 나이퀴스트 조건을 만족하는가 — 심볼 순간의
    ISI 가 0 인가. 정합 필터 쌍이라는 말의 뜻이 이것이다

허용 오차를 낮춰서 통과시키지 말 것 (PLAN.md §0.6).
"""
import cmath
import math
import unittest

from wirelesslib import dsp


class TestFFT(unittest.TestCase):
    def test_fft_matches_naive_dft(self):
        """빠른 것과 느린 것이 같은 답을 내야 한다."""
        rnd = __import__('random').Random(20260916)
        for n in (2, 4, 8, 16, 64, 256):
            x = [complex(rnd.gauss(0, 1), rnd.gauss(0, 1))
                 for _ in range(n)]
            fast, slow = dsp.fft(x), dsp.dft(x)
            for a, b in zip(fast, slow):
                self.assertLess(abs(a - b), 1e-9)

    def test_ifft_is_inverse(self):
        rnd = __import__('random').Random(7)
        x = [complex(rnd.gauss(0, 1), rnd.gauss(0, 1))
             for _ in range(128)]
        y = dsp.ifft(dsp.fft(x))
        for a, b in zip(x, y):
            self.assertLess(abs(a - b), 1e-9)

    def test_idft_handles_non_power_of_two(self):
        """SC-FDMA 의 DFT 크기는 2의 거듭제곱이 아니다 (12의 배수)."""
        rnd = __import__('random').Random(72)
        for n in (12, 36, 72, 180):
            x = [complex(rnd.gauss(0, 1), rnd.gauss(0, 1))
                 for _ in range(n)]
            y = dsp.any_idft(dsp.any_dft(x))
            for a, b in zip(x, y):
                self.assertLess(abs(a - b), 1e-9)

    def test_fft_of_single_tone(self):
        """정확히 k번째 빈에 놓인 정현파는 그 빈에만 에너지가 있다."""
        n, k = 64, 5
        x = [cmath.exp(2j * math.pi * k * i / n) for i in range(n)]
        X = dsp.fft(x)
        self.assertLess(abs(abs(X[k]) - n), 1e-9)
        for j in range(n):
            if j != k:
                self.assertLess(abs(X[j]), 1e-9)

    def test_length_must_be_power_of_two(self):
        with self.assertRaises(ValueError):
            dsp.fft([1, 2, 3])

    def test_empty_and_single(self):
        self.assertEqual(dsp.fft([]), [])
        self.assertEqual(dsp.fft([3 + 0j]), [3 + 0j])


class TestConv(unittest.TestCase):
    def test_conv_matches_polynomial_product(self):
        # (1 + 2x)(1 + 3x + 4x²) = 1 + 5x + 10x² + 8x³
        got = dsp.conv([1, 2], [1, 3, 4])
        for a, b in zip(got, [1, 5, 10, 8]):
            self.assertAlmostEqual(a, b, places=12)

    def test_conv_length(self):
        self.assertEqual(len(dsp.conv([0] * 5, [0] * 3)), 7)

    def test_conv_with_empty(self):
        self.assertEqual(dsp.conv([], [1, 2]), [])


class TestPulses(unittest.TestCase):
    def test_rc_is_nyquist(self):
        """상승 코사인은 심볼 순간(0 말고)에서 0 이어야 한다."""
        sps, span = 8, 10
        for beta in (0.0, 0.22, 0.35, 1.0):
            h = dsp.rc(beta, sps, span)
            mid = len(h) // 2
            for k in range(1, span // 2 + 1):
                self.assertLess(abs(h[mid + k * sps]), 1e-9,
                                'beta=%s k=%d' % (beta, k))

    def _isi(self, span, beta=0.25, sps=8, kmax=4):
        """정합 필터 쌍을 이은 뒤 심볼 순간에 남는 최대 ISI(상대값)."""
        g = dsp.rrc(beta, sps, span)
        y = dsp.conv(g, g)
        mid = len(y) // 2
        peak = y[mid]
        self.assertGreater(peak, 0)
        return max(abs(y[mid + k * sps] / peak)
                   for k in range(1, kmax + 1))

    def test_rrc_pair_is_nyquist(self):
        """RRC 두 개를 이어 붙이면(정합 필터) ISI 가 0 에 가깝다."""
        self.assertLess(self._isi(12), 2e-3)

    def test_rrc_isi_shrinks_as_span_grows(self):
        """남는 ISI 는 오직 잘라 낸 탓이다 — 길게 자르면 줄어든다.

        꼬리 쪽(k 가 span/2 에 가까운 자리)은 컨볼루션이 겹칠 구간을
        다 써 버려서 값이 커진다. 그것은 펄스의 성질이 아니라 자른
        길이의 성질이므로, 허용 오차를 늘리는 대신 '길이를 늘리면
        줄어든다' 는 진짜 성질을 확인한다.
        """
        got = [self._isi(s) for s in (12, 16, 24, 32)]
        for a, b in zip(got, got[1:]):
            self.assertLess(b, a)
        self.assertLess(got[-1], 3e-5)

    def test_rrc_energy_is_one(self):
        g = dsp.rrc(0.25, 8, 12)
        e = sum(v * v for v in g)
        self.assertAlmostEqual(e, 1.0, places=9)

    def test_rc_beta_zero_is_sinc(self):
        h = dsp.rc(0.0, 4, 8)
        mid = len(h) // 2
        for i, v in enumerate(h):
            t = (i - mid) / 4.0
            want = (1.0 if t == 0
                    else math.sin(math.pi * t) / (math.pi * t))
            self.assertAlmostEqual(v, want, places=12)


class TestResample(unittest.TestCase):
    def test_upsample_inserts_zeros(self):
        self.assertEqual(dsp.upsample([1, 2], 3), [1, 0, 0, 2, 0, 0])

    def test_downsample_takes_every_nth(self):
        self.assertEqual(dsp.downsample([1, 0, 0, 2, 0, 0], 3), [1, 2])

    def test_roundtrip(self):
        x = [1, -1, 1, -1]
        self.assertEqual(dsp.downsample(dsp.upsample(x, 4), 4), x)

    def test_factor_must_be_positive(self):
        with self.assertRaises(ValueError):
            dsp.upsample([1], 0)


class TestPeriodogram(unittest.TestCase):
    def test_tone_lands_in_its_bin(self):
        n, k = 128, 11
        x = [cmath.exp(2j * math.pi * k * i / n) for i in range(n)]
        p = dsp.periodogram(x)
        self.assertEqual(max(range(n), key=lambda j: p[j]), k)

    def test_parseval(self):
        """시간 영역 에너지와 주파수 영역 에너지가 같아야 한다."""
        rnd = __import__('random').Random(3)
        x = [complex(rnd.gauss(0, 1), rnd.gauss(0, 1))
             for _ in range(64)]
        et = sum(abs(v) ** 2 for v in x)
        ef = sum(dsp.periodogram(x)) * len(x)
        self.assertAlmostEqual(et, ef, places=9)


if __name__ == '__main__':
    unittest.main()
