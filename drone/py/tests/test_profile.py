# -*- coding: utf-8 -*-
"""profile 시험 — 사다리꼴 속도 프로파일 (T28) 과 정규화한 β."""
import math
import unittest

from droneshow import poly, profile


class Trapezoid(unittest.TestCase):
    def test_trapezoid_time_formula(self):
        pr = profile.trapezoid(10.0, 3.0, 2.0)
        self.assertFalse(pr['triangular'])
        self.assertAlmostEqual(pr['T'], 10 / 3 + 3 / 2, places=14)
        self.assertAlmostEqual(pr['v_peak'], 3.0)

    def test_triangular_case(self):
        # d < v²/a 이면 최고 속도에 닿기 전에 줄여야 한다
        pr = profile.trapezoid(2.0, 3.0, 2.0)
        self.assertTrue(pr['triangular'])
        self.assertAlmostEqual(pr['T'], 2 * math.sqrt(2 / 2), places=14)
        self.assertAlmostEqual(pr['v_peak'], math.sqrt(2 * 2),
                               places=14)

    def test_boundary_case_is_both(self):
        a = profile.trapezoid(4.5, 3.0, 2.0)          # d = v²/a
        self.assertAlmostEqual(a['T'], 3.0, places=14)

    def test_samples_respect_limits_and_arrive(self):
        for d in (0.5, 4.5, 12.0):
            pr = profile.trapezoid(d, 3.0, 2.0)
            n = 400
            for k in range(n + 1):
                s, v, a = profile.sample(pr, pr['T'] * k / n)
                self.assertLessEqual(v, 3.0 + 1e-12)
                self.assertLessEqual(abs(a), 2.0 + 1e-12)
            s, v, _a = profile.sample(pr, pr['T'])
            self.assertAlmostEqual(s, d, places=12)
            self.assertAlmostEqual(v, 0.0, places=12)

    def test_polynomial_profile_is_slower(self):
        # 같은 한계에서 최소 스냅 β 로 가면 사다리꼴보다 오래 걸린다
        for d in (0.5, 4.5, 12.0):
            t_trap = profile.trapezoid(d, 3.0, 2.0)['T']
            t_snap = profile.feasible_time(d, 3.0, 2.0,
                                           poly.rest_to_rest(4))
            self.assertGreater(t_snap, t_trap)


class Beta(unittest.TestCase):
    def test_beta_trap_ends_and_middle(self):
        self.assertEqual(profile.beta_trap(0.0, 0.25), 0.0)
        self.assertAlmostEqual(profile.beta_trap(1.0, 0.25), 1.0,
                               places=15)
        self.assertAlmostEqual(profile.beta_trap(0.5, 0.25), 0.5,
                               places=15)

    def test_beta_trap_continuous(self):
        r = 0.3
        for u in (r, 1 - r):
            a = profile.beta_trap(u - 1e-9, r)
            b = profile.beta_trap(u + 1e-9, r)
            self.assertAlmostEqual(a, b, places=7)

    def test_beta_limits(self):
        # β' 최대 = 1/(1−r), β'' 최대 = 1/(r(1−r))
        d1, d2 = profile.beta_trap_limits(0.25)
        self.assertAlmostEqual(d1, 1 / 0.75)
        self.assertAlmostEqual(d2, 1 / (0.25 * 0.75))

    def test_poly_beta_limits(self):
        d1, d2 = profile.poly_limits(poly.rest_to_rest(4))
        self.assertAlmostEqual(d1, 2.1875, places=6)       # β'(½)
        self.assertGreater(d2, 7.0)


if __name__ == '__main__':
    unittest.main()
