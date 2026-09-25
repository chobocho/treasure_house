# -*- coding: utf-8 -*-
"""poly 시험 — 최소 저크·최소 스냅 다항식 (T27 의 증인)."""
import math
import unittest

from droneshow import poly
from droneshow import rng


class RestToRest(unittest.TestCase):
    def test_min_jerk_closed_form(self):
        c = poly.rest_to_rest(3)
        for a, b in zip(c, [0, 0, 0, 10, -15, 6]):
            self.assertAlmostEqual(a, b, places=11)

    def test_min_snap_closed_form(self):
        c = poly.rest_to_rest(4)
        for a, b in zip(c, [0, 0, 0, 0, 35, -84, 70, -20]):
            self.assertAlmostEqual(a, b, places=10)

    def test_boundary_derivatives_vanish(self):
        c = poly.rest_to_rest(4)
        for k in range(1, 4):
            d = poly.deriv(c, k)
            self.assertAlmostEqual(poly.val(d, 0.0), 0.0, places=10)
            self.assertAlmostEqual(poly.val(d, 1.0), 0.0, places=9)
        self.assertAlmostEqual(poly.val(c, 1.0), 1.0, places=10)

    def test_symmetry(self):
        # β(u) + β(1−u) = 1 — 가는 길과 오는 길이 똑같이 생겼다
        c = poly.rest_to_rest(4)
        for u in (0.1, 0.3, 0.45):
            self.assertAlmostEqual(poly.val(c, u) + poly.val(c, 1 - u),
                                   1.0, places=10)


class Calculus(unittest.TestCase):
    def test_deriv_and_val(self):
        c = [1.0, 2.0, 3.0]                  # 1 + 2t + 3t²
        self.assertEqual(poly.deriv(c, 1), [2.0, 6.0])
        self.assertEqual(poly.val(c, 2.0), 17.0)
        self.assertEqual(poly.deriv(c, 3), [0.0])

    def test_eighth_derivative_is_zero(self):
        c = poly.rest_to_rest(4)
        self.assertEqual(poly.deriv(c, 8), [0.0])

    def test_integral_of_product(self):
        # ∫₀² (1+t)(t) dt = 2 + 8/3
        got = poly.int_prod([1.0, 1.0], [0.0, 1.0], 2.0)
        self.assertAlmostEqual(got, 2 + 8 / 3, places=14)


def bump(t, big_t, a):
    """[0, T] 양 끝에서 값과 1~3계 도함수가 0 인 섭동 (다항식)."""
    u = t / big_t
    return a * (u * (1 - u)) ** 4


class Optimality(unittest.TestCase):
    """T27 — 7차 다항식은 끝점 조건을 지키는 모든 곡선 중 스냅 제곱
    적분이 가장 작다."""

    def test_cross_term_vanishes(self):
        # ∫ x⁗ h⁗ = 0 (네 번 부분적분) — 그래서 J(x+h) = J(x) + J(h)
        big_t = 3.0
        c = [2.0 * a / big_t ** k
             for k, a in enumerate(poly.rest_to_rest(4))]
        g = rng.Rng(5)
        for _ in range(5):
            h = poly.bump_poly(big_t, [g.normal() for _ in range(4)])
            cross = poly.int_prod(poly.deriv(c, 4), poly.deriv(h, 4),
                                  big_t)
            # 크기의 기준은 √(J(x)·J(h)) — 부동소수 자릿수 안에서 0
            scale = math.sqrt(poly.snap_cost(c, big_t)
                              * poly.snap_cost(h, big_t))
            self.assertLess(abs(cross) / scale, 1e-9)

    def test_random_perturbations_never_lower_cost(self):
        big_t = 2.0
        c = [a / big_t ** k for k, a in enumerate(poly.rest_to_rest(4))]
        j0 = poly.snap_cost(c, big_t)
        g = rng.Rng(6)
        for _ in range(50):
            h = poly.bump_poly(big_t, [g.normal() for _ in range(4)])
            eps = 0.1 * g.normal()
            pert = poly.add(c, [eps * x for x in h])
            self.assertGreaterEqual(poly.snap_cost(pert, big_t), j0)


class MultiSegment(unittest.TestCase):
    def setUp(self):
        self.wp = [0.0, 2.0, 1.0, 4.0]
        self.times = [1.5, 1.0, 2.0]
        self.segs = poly.min_snap(self.wp, self.times)

    def test_passes_through_waypoints(self):
        for k, c in enumerate(self.segs):
            self.assertAlmostEqual(poly.val(c, 0.0), self.wp[k],
                                   places=9)
            self.assertAlmostEqual(poly.val(c, self.times[k]),
                                   self.wp[k + 1], places=9)

    def test_rest_at_both_ends(self):
        first, last = self.segs[0], self.segs[-1]
        for k in range(1, 4):
            self.assertAlmostEqual(poly.val(poly.deriv(first, k), 0.0),
                                   0.0, places=9)
            self.assertAlmostEqual(
                poly.val(poly.deriv(last, k), self.times[-1]), 0.0,
                places=8)

    def test_smooth_up_to_sixth_derivative(self):
        for k in range(len(self.segs) - 1):
            a, b = self.segs[k], self.segs[k + 1]
            for d in range(1, 7):
                left = poly.val(poly.deriv(a, d), self.times[k])
                right = poly.val(poly.deriv(b, d), 0.0)
                self.assertAlmostEqual(left, right, places=6)

    def test_single_segment_is_scaled_beta(self):
        (c,) = poly.min_snap([1.0, 4.0], [2.0])
        beta = poly.rest_to_rest(4)
        for t in (0.3, 1.0, 1.7):
            want = 1 + 3 * poly.val(beta, t / 2)
            self.assertAlmostEqual(poly.val(c, t), want, places=9)

    def test_perturbation_through_waypoints_costs_more(self):
        j0 = sum(poly.snap_cost(c, t) for c, t in zip(self.segs,
                                                       self.times))
        g = rng.Rng(8)
        for _ in range(20):
            segs = [poly.add(c, poly.bump_poly(t, [0.2 * g.normal()
                                                   for _ in range(4)]))
                    for c, t in zip(self.segs, self.times)]
            j = sum(poly.snap_cost(c, t)
                    for c, t in zip(segs, self.times))
            self.assertGreater(j, j0)


if __name__ == '__main__':
    unittest.main()
