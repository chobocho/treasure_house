# -*- coding: utf-8 -*-
"""자동미분 — 손으로 유도한 도함수와 정확히 같은 값을 내야 한다.

   수치미분과 달리 절단오차가 없다. 그래서 '거의 같다'가 아니라
   '기계정밀도까지 같다'를 요구한다.
"""
import math
import unittest

from py import autodiff as ad
from py import funcs
from py import linalg as la
from py import numdiff as nd


class TestForward(unittest.TestCase):
    def test_polynomial(self):
        f = lambda x: 3.0 * x[0] ** 3 - 2.0 * x[0] + 5.0
        g = ad.grad_forward(f, [2.0])
        self.assertAlmostEqual(g[0], 9.0 * 4.0 - 2.0, places=12)

    def test_two_vars(self):
        f = lambda x: x[0] * x[1] + ad.sin(x[0])
        g = ad.grad_forward(f, [0.3, -1.7])
        self.assertAlmostEqual(g[0], -1.7 + math.cos(0.3), places=12)
        self.assertAlmostEqual(g[1], 0.3, places=12)

    def test_division_and_exp(self):
        f = lambda x: ad.exp(x[0]) / (1.0 + x[1] ** 2)
        g = ad.grad_forward(f, [0.5, 2.0])
        self.assertAlmostEqual(g[0], math.exp(0.5) / 5.0, places=12)
        self.assertAlmostEqual(g[1], -math.exp(0.5) * 4.0 / 25.0, places=12)

    def test_matches_analytic_rosenbrock(self):
        p = funcs.Rosenbrock(4)
        x = [0.3, -0.7, 1.4, 0.2]
        g_ad = ad.grad_forward(p.f, x)
        g_an = p.grad(x)
        self.assertLess(la.norm(la.vsub(g_ad, g_an)), 1e-12)

    def test_beats_finite_difference(self):
        # 자동미분은 절단오차가 없다 — 수치미분보다 정확해야 한다.
        p = funcs.Rosenbrock(2)
        x = [0.37, -0.81]
        exact = p.grad(x)
        e_ad = la.norm(la.vsub(ad.grad_forward(p.f, x), exact))
        e_fd = la.norm(la.vsub(nd.grad(p.f, x), exact))
        self.assertLess(e_ad, 1e-13)
        self.assertGreater(e_fd, e_ad)


class TestReverse(unittest.TestCase):
    def test_matches_forward(self):
        p = funcs.Rosenbrock(5)
        x = [0.3, -0.7, 1.4, 0.2, -1.1]
        gf = ad.grad_forward(p.f, x)
        gr = ad.grad_reverse(p.f, x)
        self.assertLess(la.norm(la.vsub(gf, gr)), 1e-13)

    def test_one_pass_only(self):
        # 역방향은 함수를 '한 번'만 평가한다 — 그것이 존재 이유다.
        calls = [0]

        def f(x):
            calls[0] += 1
            return x[0] ** 2 + x[1] ** 2 + x[2] ** 2

        ad.grad_reverse(f, [1.0, 2.0, 3.0])
        self.assertEqual(calls[0], 1)

    def test_forward_costs_n_passes(self):
        calls = [0]

        def f(x):
            calls[0] += 1
            return x[0] ** 2 + x[1] ** 2 + x[2] ** 2

        ad.grad_forward(f, [1.0, 2.0, 3.0])
        self.assertEqual(calls[0], 3)          # 변수 하나에 한 번씩

    def test_shared_subexpression(self):
        # 같은 중간값을 여러 번 쓰는 그래프에서도 정확해야 한다
        def f(x):
            t = ad.exp(x[0] * x[1])
            return t * t + t
        x = [0.4, 1.3]
        z = math.exp(0.4 * 1.3)
        self.assertAlmostEqual(ad.grad_reverse(f, x)[0], (2 * z * z + z) * 1.3, places=11)
        self.assertAlmostEqual(ad.grad_reverse(f, x)[1], (2 * z * z + z) * 0.4, places=11)

    def test_logistic_problem(self):
        p = funcs.LogisticRegression.toy(seed=3, n=50, d=3)
        x = [0.4, -0.2, 0.9]
        # f 를 자동미분이 통과할 수 있는 형태로 다시 쓴다
        def f(w):
            s = 0.0
            for i in range(len(p.X)):
                z = p.y[i] * sum(a * b for a, b in zip(w, p.X[i]))
                s = s + ad.log(1.0 + ad.exp(-z))
            return s / len(p.X) + 0.5 * p.lam * sum(v * v for v in w)
        self.assertLess(la.norm(la.vsub(ad.grad_reverse(f, x), p.grad(x))), 1e-10)


if __name__ == '__main__':
    unittest.main()
