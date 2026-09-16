# -*- coding: utf-8 -*-
"""spread 모듈의 증인 시험.

확산 부호는 "그럴듯해 보이는데 성질이 없는" 수열을 만들기 아주 쉬운
자리다. 탭 하나만 틀려도 주기가 짧아지고, 짧아진 것은 눈으로 안 보인다.
그래서 성질을 하나하나 기계로 확인한다.

  · 왈시 부호가 서로 직교하는가
  · OVSF 는 조상·자손 관계가 아닐 때만 직교하는가
  · 되먹임 다항식이 **정말 원시 다항식인가** — 그래야 주기가 2^m−1 이다.
    IS-95 의 숏 PN(2¹⁵−1)과 롱코드(2⁴²−1)의 탭을 이걸로 검산한다
  · m-수열의 자기상관이 두 값(N, −1)만 갖는가
  · 골드 부호의 상호상관이 세 값만 갖는가
  · Zadoff-Chu 가 일정 진폭이고 순환 자기상관이 0 인가
"""
import cmath
import math
import unittest

from wirelesslib import spread


class TestWalsh(unittest.TestCase):
    def test_hadamard_is_orthogonal(self):
        for n in (2, 4, 8, 64):
            h = spread.hadamard(n)
            self.assertEqual(len(h), n)
            for i in range(n):
                self.assertEqual(sum(v * v for v in h[i]), n)
                for j in range(i + 1, n):
                    dot = sum(a * b for a, b in zip(h[i], h[j]))
                    self.assertEqual(dot, 0, '%d·%d' % (i, j))

    def test_entries_are_plus_minus_one(self):
        for row in spread.hadamard(8):
            for v in row:
                self.assertIn(v, (1, -1))

    def test_row_zero_is_all_ones(self):
        self.assertEqual(spread.walsh(64, 0), [1] * 64)

    def test_size_must_be_power_of_two(self):
        with self.assertRaises(ValueError):
            spread.hadamard(6)


class TestOVSF(unittest.TestCase):
    def test_length_is_spreading_factor(self):
        for sf in (4, 8, 16, 512):
            self.assertEqual(len(spread.ovsf(sf, 3)), sf)

    def test_same_level_codes_are_orthogonal(self):
        for sf in (4, 8, 16):
            for i in range(sf):
                for j in range(i + 1, sf):
                    a, b = spread.ovsf(sf, i), spread.ovsf(sf, j)
                    dot = sum(x * y for x, y in zip(a, b))
                    self.assertEqual(dot, 0)

    def test_ancestor_codes_collide(self):
        """조상을 쓰면 자손을 못 쓴다 — OVSF 배정 규칙의 뿌리.

        긴 부호의 앞머리가 짧은 부호와 똑같아진다. 그러면 짧은 쪽
        수신기가 긴 쪽 신호를 자기 것으로 알아듣는다.
        """
        parent = spread.ovsf(4, 1)
        child = spread.ovsf(8, 2)
        self.assertTrue(spread.is_ancestor(4, 1, 8, 2))
        head = child[:4]
        self.assertEqual(sum(x * y for x, y in zip(parent, head)), 4)

    def test_non_ancestor_across_levels_is_orthogonal(self):
        self.assertFalse(spread.is_ancestor(4, 1, 8, 4))
        parent = spread.ovsf(4, 1)
        other = spread.ovsf(8, 4)
        for half in (other[:4], other[4:]):
            self.assertEqual(sum(x * y for x, y in zip(parent, half)),
                             0)


class TestPrimitive(unittest.TestCase):
    def test_known_primitive_polynomials(self):
        self.assertTrue(spread.is_primitive(0b1011, 3))       # x³+x+1
        self.assertTrue(spread.is_primitive(0b10011, 4))      # x⁴+x+1
        self.assertTrue(spread.is_primitive(0b100101, 5))     # x⁵+x²+1

    def test_known_non_primitive(self):
        # x⁴+x³+x²+x+1 은 기약이지만 원시가 아니다 (주기 5)
        self.assertFalse(spread.is_primitive(0b11111, 4))
        # x⁴+1 = (x+1)⁴ — 기약도 아니다
        self.assertFalse(spread.is_primitive(0b10001, 4))

    def test_is95_short_pn_taps_are_primitive(self):
        """IS-95 숏 PN 의 탭이 맞다면 주기가 2¹⁵−1 이어야 한다."""
        self.assertTrue(spread.is_primitive(spread.IS95_PN_I, 15))
        self.assertTrue(spread.is_primitive(spread.IS95_PN_Q, 15))

    def test_is95_long_code_taps_are_primitive(self):
        """2⁴²−1 은 돌려서 못 센다 — 대수로 확인한다."""
        self.assertTrue(spread.is_primitive(spread.IS95_LONG, 42))

    def test_gsm_and_wcdma_polynomials(self):
        self.assertTrue(spread.is_primitive(spread.WCDMA_X, 18))
        self.assertTrue(spread.is_primitive(spread.WCDMA_Y, 18))


class TestMSequence(unittest.TestCase):
    def test_period_is_maximal(self):
        for poly, m in ((0b1011, 3), (0b10011, 4), (0b100101, 5),
                        (0b1000011, 6), (spread.IS95_PN_I, 15)):
            self.assertEqual(spread.lfsr_period(poly, m), (1 << m) - 1)

    def test_balance_property(self):
        """한 주기에 1 이 0 보다 정확히 하나 많다."""
        for m in (5, 7, 10):
            poly = {5: 0b100101, 7: 0b10000011, 10: 0b10000001001}[m]
            s = spread.m_sequence(poly, m)
            self.assertEqual(sum(s) - (len(s) - sum(s)), 1)

    def test_autocorrelation_is_two_valued(self):
        """m-수열의 자기상관은 N 과 −1 둘뿐이다."""
        s = spread.bipolar(spread.m_sequence(0b10000011, 7))
        n = len(s)
        vals = set()
        for lag in range(n):
            vals.add(sum(s[i] * s[(i + lag) % n] for i in range(n)))
        self.assertEqual(sorted(vals), [-1, n])

    def test_shifting_gives_another_shift_of_itself(self):
        """이동-덧셈 성질.

        m-수열은 제 이동본과 XOR 해도 또 제 이동본이다.
        """
        s = spread.m_sequence(0b100101, 5)
        n = len(s)
        a = [s[(i + 3) % n] ^ s[(i + 7) % n] for i in range(n)]
        shifts = [[s[(i + k) % n] for i in range(n)] for k in range(n)]
        self.assertIn(a, shifts)


class TestGold(unittest.TestCase):
    def test_cross_correlation_is_three_valued(self):
        """골드 부호의 상호상관은 세 값만 갖는다 — 그래서 쓸 만하다."""
        m = 5
        codes = [spread.gold(0b100101, 0b111101, m, k)
                 for k in range(6)]
        vals = set()
        for i in range(len(codes)):
            for j in range(i + 1, len(codes)):
                a = spread.bipolar(codes[i])
                b = spread.bipolar(codes[j])
                n = len(a)
                for lag in range(n):
                    vals.add(sum(a[t] * b[(t + lag) % n]
                                 for t in range(n)))
        self.assertLessEqual(len(vals), 3)
        self.assertEqual(sorted(vals), [-9, -1, 7])

    def test_family_size(self):
        m = 5
        n = (1 << m) - 1
        self.assertEqual(len(spread.gold_family(0b100101, 0b111101, m)),
                         n + 2)


class TestZadoffChu(unittest.TestCase):
    def test_constant_amplitude(self):
        for n, u in ((63, 25), (139, 34), (839, 1)):
            for v in spread.zadoff_chu(n, u):
                self.assertAlmostEqual(abs(v), 1.0, places=12)

    def test_zero_cyclic_autocorrelation(self):
        for n, u in ((63, 25), (139, 34)):
            x = spread.zadoff_chu(n, u)
            for lag in range(1, n):
                s = sum(x[i] * x[(i + lag) % n].conjugate()
                        for i in range(n))
                self.assertLess(abs(s), 1e-9, 'N=%d lag=%d' % (n, lag))

    def test_cross_correlation_is_sqrt_n(self):
        """서로 다른 근(root)끼리는 상호상관 크기가 √N 으로 고르다."""
        n = 139
        a = spread.zadoff_chu(n, 1)
        b = spread.zadoff_chu(n, 34)
        for lag in range(n):
            s = sum(a[i] * b[(i + lag) % n].conjugate()
                    for i in range(n))
            self.assertAlmostEqual(abs(s), math.sqrt(n), places=6)

    def test_dft_of_zc_is_zc(self):
        """ZC 의 DFT 도 ZC 다.

        시간에서도 주파수에서도 진폭이 고르다.
        """
        from wirelesslib import dsp
        n, u = 64, 25
        x = spread.zadoff_chu(n, u)
        X = dsp.fft(x)
        mags = [abs(v) / math.sqrt(n) for v in X]
        for v in mags:
            self.assertAlmostEqual(v, 1.0, places=9)

    def test_root_must_be_coprime(self):
        with self.assertRaises(ValueError):
            spread.zadoff_chu(63, 21)      # gcd(63,21)=21


class TestProcessingGain(unittest.TestCase):
    def test_gain_is_ten_log_sf(self):
        self.assertAlmostEqual(spread.processing_gain_db(128),
                               10 * math.log10(128), places=12)

    def test_is95_forward_gain(self):
        """1.2288 Mcps / 9600 bps = 128 → 21 dB."""
        self.assertAlmostEqual(
            spread.processing_gain_db(1228800.0 / 9600.0), 21.07,
            places=2)


if __name__ == '__main__':
    unittest.main()
