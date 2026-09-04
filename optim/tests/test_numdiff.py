# -*- coding: utf-8 -*-
"""수치미분과 시험함수 — 해석적 도함수가 맞는지 기계로 검사한다.

   최적화 코드에서 가장 흔한 버그는 알고리즘이 아니라 '기울기 식을 잘못 적은 것'이다.
   그래서 이 파일은 앞으로 모든 부에서 쓰일 안전망이다.
"""
import math
import unittest

from py import numdiff as nd
from py import funcs
from py import linalg as la


class TestFiniteDifference(unittest.TestCase):
    def test_grad_quadratic(self):
        f = lambda x: x[0] ** 2 + 3.0 * x[1] ** 2
        g = nd.grad(f, [1.0, 2.0])
        self.assertAlmostEqual(g[0], 2.0, places=6)
        self.assertAlmostEqual(g[1], 12.0, places=6)

    def test_forward_is_worse_than_central(self):
        # 이론: 전진차분 오차 O(h)+O(ε/h) → ~√ε,  중심차분 → ~ε^(2/3)
        f = lambda x: math.exp(x[0])
        x = [0.7]
        exact = math.exp(0.7)
        ef = abs(nd.grad_forward(f, x)[0] - exact)
        ec = abs(nd.grad(f, x)[0] - exact)
        self.assertLess(ec, ef)

    def test_hessian_symmetric(self):
        f = lambda x: x[0] ** 2 * x[1] + x[1] ** 3
        H = nd.hessian(f, [1.5, -0.5])
        self.assertAlmostEqual(H[0][1], H[1][0], places=5)
        self.assertAlmostEqual(H[0][0], 2.0 * (-0.5), places=4)   # ∂²f/∂x² = 2y

    def test_jacobian(self):
        F = lambda x: [x[0] * x[1], x[0] + x[1] ** 2]
        J = nd.jacobian(F, [2.0, 3.0])
        self.assertAlmostEqual(J[0][0], 3.0, places=5)
        self.assertAlmostEqual(J[0][1], 2.0, places=5)
        self.assertAlmostEqual(J[1][1], 6.0, places=5)

    def test_zero_point(self):
        # x=0 에서도 스텝이 0 이 되지 않아야 한다(상대 스텝만 쓰면 h=0 이 된다)
        f = lambda x: x[0] ** 3
        self.assertAlmostEqual(nd.grad(f, [0.0])[0], 0.0, places=6)

    def test_complex_step_exact(self):
        # 복소 스텝은 뺄셈 상쇄가 없어 h 를 1e-30 까지 줄일 수 있다.
        f = lambda x: x[0] ** 3 * 2.0
        g = nd.grad_complex(f, [1.3])
        self.assertAlmostEqual(g[0], 6.0 * 1.3 ** 2, places=12)


class TestCheckGrad(unittest.TestCase):
    def test_correct_gradient_passes(self):
        p = funcs.Rosenbrock(2)
        self.assertLess(nd.check_grad(p.f, p.grad, [0.3, -0.7]), 1e-6)

    def test_wrong_gradient_fails(self):
        bad = lambda x: [1.0, 1.0]
        p = funcs.Rosenbrock(2)
        self.assertGreater(nd.check_grad(p.f, bad, [0.3, -0.7]), 1e-2)

    def test_check_hess(self):
        p = funcs.Rosenbrock(2)
        self.assertLess(nd.check_hess(p.grad, p.hess, [0.3, -0.7]), 1e-5)


class TestProblems(unittest.TestCase):
    """모든 시험함수의 해석적 기울기·헤세를 수치미분과 대조한다."""

    def _consistent(self, p, pts):
        for x in pts:
            self.assertLess(nd.check_grad(p.f, p.grad, x), 1e-5,
                            '%s 기울기 불일치 @%r' % (p.name, x))
            if p.hess is not None:
                self.assertLess(nd.check_hess(p.grad, p.hess, x), 1e-4,
                                '%s 헤세 불일치 @%r' % (p.name, x))

    def test_rosenbrock(self):
        self._consistent(funcs.Rosenbrock(2), [[0.5, 0.5], [-1.2, 1.0], [2.0, 3.0]])
        self._consistent(funcs.Rosenbrock(5), [[0.3] * 5, [1.1, -0.4, 0.9, 0.2, -1.0]])

    def test_quadratic(self):
        Q = [[4.0, 1.0], [1.0, 3.0]]
        p = funcs.Quadratic(Q, [1.0, 2.0])
        self._consistent(p, [[0.0, 0.0], [1.0, -1.0]])
        # 최적해는 Qx = c
        xs = la.solve(Q, [1.0, 2.0])
        self.assertLess(la.norm(p.grad(xs)), 1e-10)

    def test_himmelblau_and_beale(self):
        self._consistent(funcs.Himmelblau(), [[0.0, 0.0], [3.0, 2.0], [-1.0, 4.0]])
        self._consistent(funcs.Beale(), [[1.0, 0.5], [0.0, 0.0]])

    def test_logistic(self):
        p = funcs.LogisticRegression.toy(seed=7, n=40, d=3)
        self._consistent(p, [[0.0, 0.0, 0.0], [0.5, -0.3, 0.8]])

    def test_known_minima(self):
        r = funcs.Rosenbrock(2)
        self.assertAlmostEqual(r.f([1.0, 1.0]), 0.0, places=12)
        self.assertLess(la.norm(r.grad([1.0, 1.0])), 1e-12)
        h = funcs.Himmelblau()
        self.assertAlmostEqual(h.f([3.0, 2.0]), 0.0, places=12)


if __name__ == '__main__':
    unittest.main()
