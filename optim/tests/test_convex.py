# -*- coding: utf-8 -*-
"""볼록성 도구 — 수치 검사와 투영.

   투영은 5부(투영경사)·8부(근접경사)에서 그대로 쓰이므로 여기서 확실히 못박는다.
"""
import math
import random
import unittest

from py import convex as cx
from py import funcs
from py import linalg as la


class TestJensen(unittest.TestCase):
    def test_convex_passes(self):
        f = lambda x: x[0] ** 2 + x[1] ** 2
        self.assertTrue(cx.looks_convex(f, 2, trials=200, seed=1))

    def test_nonconvex_caught(self):
        f = lambda x: math.sin(3.0 * x[0]) + 0.1 * x[1] ** 2
        self.assertFalse(cx.looks_convex(f, 2, trials=400, seed=1, scale=4.0))

    def test_violation_value(self):
        f = lambda x: -x[0] ** 2                       # 오목함수
        v = cx.jensen_gap(f, [-1.0], [1.0], 0.5)
        self.assertLess(v, 0.0)                        # f(중점) > 평균 → 음수 간격

    def test_linear_is_both(self):
        f = lambda x: 3.0 * x[0] - 2.0 * x[1]
        self.assertAlmostEqual(cx.jensen_gap(f, [1.0, 2.0], [-3.0, 0.5], 0.3), 0.0, places=12)


class TestCurvatureEstimates(unittest.TestCase):
    def test_quadratic_constants(self):
        Q = [[3.0, 0.0], [0.0, 7.0]]
        p = funcs.Quadratic(Q)
        mu, L = cx.curvature_range(p, [[0.0, 0.0], [1.0, -1.0], [2.0, 3.0]])
        self.assertAlmostEqual(mu, 3.0, places=8)
        self.assertAlmostEqual(L, 7.0, places=8)

    def test_rosenbrock_indefinite(self):
        p = funcs.Rosenbrock(2)
        mu, L = cx.curvature_range(p, [[0.0, 1.0]])
        self.assertLess(mu, 0.0)                        # 부정부호 → 볼록이 아니다


class TestProjections(unittest.TestCase):
    def test_box(self):
        self.assertEqual(cx.proj_box([2.0, -3.0, 0.5], -1.0, 1.0), [1.0, -1.0, 0.5])

    def test_ball_inside_unchanged(self):
        x = [0.3, 0.4]
        self.assertEqual(cx.proj_ball(x, 1.0), x)

    def test_ball_outside(self):
        p = cx.proj_ball([3.0, 4.0], 2.0)
        self.assertAlmostEqual(la.norm(p), 2.0, places=12)
        self.assertAlmostEqual(p[0] / p[1], 3.0 / 4.0, places=12)   # 방향 보존

    def test_simplex_basic(self):
        p = cx.proj_simplex([0.5, 0.5, 0.5])
        self.assertAlmostEqual(sum(p), 1.0, places=12)
        for v in p:
            self.assertAlmostEqual(v, 1.0 / 3.0, places=12)

    def test_simplex_clips_negative(self):
        p = cx.proj_simplex([1.0, -2.0, 0.5])
        self.assertAlmostEqual(sum(p), 1.0, places=12)
        self.assertTrue(all(v >= -1e-15 for v in p))
        self.assertAlmostEqual(p[1], 0.0, places=12)

    def test_simplex_already_on(self):
        x = [0.2, 0.3, 0.5]
        p = cx.proj_simplex(x)
        for a, b in zip(p, x):
            self.assertAlmostEqual(a, b, places=12)

    def test_simplex_is_nearest(self):
        # 무작위 점에서, 단체 위의 어떤 점도 투영보다 가깝지 않아야 한다.
        rng = random.Random(3)
        for _ in range(30):
            x = [rng.uniform(-2, 2) for _ in range(4)]
            p = cx.proj_simplex(x)
            d = la.norm(la.vsub(x, p))
            for _ in range(200):
                w = [rng.random() for _ in range(4)]
                s = sum(w)
                q = [v / s for v in w]
                self.assertLessEqual(d, la.norm(la.vsub(x, q)) + 1e-12)

    def test_projection_nonexpansive(self):
        # ‖P(x) − P(y)‖ ≤ ‖x − y‖ — 8부 근접경사 수렴 증명의 핵심 성질
        rng = random.Random(11)
        for _ in range(200):
            x = [rng.uniform(-3, 3) for _ in range(3)]
            y = [rng.uniform(-3, 3) for _ in range(3)]
            px, py = cx.proj_simplex(x), cx.proj_simplex(y)
            self.assertLessEqual(la.norm(la.vsub(px, py)), la.norm(la.vsub(x, y)) + 1e-12)


class TestSubgradient(unittest.TestCase):
    def test_abs_at_zero(self):
        g = cx.subgrad_abs([0.0])
        self.assertTrue(-1.0 <= g[0] <= 1.0)

    def test_abs_elsewhere(self):
        self.assertEqual(cx.subgrad_abs([2.0, -3.0]), [1.0, -1.0])

    def test_subgradient_inequality(self):
        # f(y) ≥ f(x) + gᵀ(y−x) 가 모든 y 에서 성립해야 한다
        f = lambda v: sum(abs(t) for t in v)
        rng = random.Random(5)
        for _ in range(300):
            x = [rng.choice([0.0, rng.uniform(-2, 2)]) for _ in range(3)]
            g = cx.subgrad_abs(x)
            y = [rng.uniform(-3, 3) for _ in range(3)]
            self.assertGreaterEqual(f(y) + 1e-12,
                                    f(x) + sum(a * (b - c) for a, b, c in zip(g, y, x)))


if __name__ == '__main__':
    unittest.main()
