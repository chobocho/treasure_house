# -*- coding: utf-8 -*-
"""무제약 최적화 알고리즘 — 이론이 말한 대로 동작하는지 검사한다.

   단순히 "수렴한다"가 아니라 이론이 예측한 성질을 확인한다:
     · 켤레기울기는 n×n 이차문제를 n 번 안에 정확히 푼다
     · 뉴턴법은 이차수렴한다 (오차의 자릿수가 매 반복 두 배)
     · 스텝 α > 2/L 이면 발산한다
     · Armijo·Wolfe 조건이 실제로 만족된다
"""
import math
import unittest

from py import funcs
from py import linalg as la
from py import unconstrained as uc


class TestLineSearch(unittest.TestCase):
    def test_armijo_condition_holds(self):
        p = funcs.Rosenbrock(2)
        x = [-1.2, 1.0]
        fx, g = p.f(x), p.grad(x)
        d = [-v for v in g]
        a, _ = uc.backtracking(p.f, x, fx, g, d)
        xn = la.axpy(a, d, x)
        self.assertLessEqual(p.f(xn), fx + 1e-4 * a * la.dot(g, d) + 1e-15)
        self.assertGreater(a, 0.0)

    def test_armijo_rejects_ascent(self):
        p = funcs.Rosenbrock(2)
        x = [-1.2, 1.0]
        with self.assertRaises(ValueError):
            uc.backtracking(p.f, x, p.f(x), p.grad(x), p.grad(x))   # 상승 방향

    def test_wolfe_conditions_hold(self):
        p = funcs.Rosenbrock(2)
        x = [-1.2, 1.0]
        fx, g = p.f(x), p.grad(x)
        d = [-v for v in g]
        a, info = uc.wolfe(p.f, p.grad, x, fx, g, d, c1=1e-4, c2=0.9)
        xn = la.axpy(a, d, x)
        self.assertLessEqual(p.f(xn), fx + 1e-4 * a * la.dot(g, d) + 1e-12)   # Armijo
        self.assertLessEqual(abs(la.dot(p.grad(xn), d)),
                             0.9 * abs(la.dot(g, d)) + 1e-9)                  # 강 곡률조건

    def test_exact_quadratic_step(self):
        # 이차함수에서 정확한 라인서치 해는 −gᵀd / dᵀQd
        Q = [[4.0, 1.0], [1.0, 3.0]]
        p = funcs.Quadratic(Q, [1.0, 2.0])
        x = [0.0, 0.0]
        g = p.grad(x)
        d = [-v for v in g]
        a, _ = uc.wolfe(p.f, p.grad, x, p.f(x), g, d)
        exact = -la.dot(g, d) / la.dot(d, la.matvec(Q, d))
        self.assertAlmostEqual(a, exact, places=6)


class TestGradientDescent(unittest.TestCase):
    def test_quadratic_converges(self):
        Q = [[4.0, 0.0], [0.0, 1.0]]
        p = funcs.Quadratic(Q, [4.0, 1.0])            # 최적해 (1, 1)
        r = uc.minimize(p, [0.0, 0.0], method='gd', step=1.0 / 4.0, tol=1e-12, maxiter=5000)
        self.assertTrue(r.converged)
        self.assertAlmostEqual(r.x[0], 1.0, places=8)
        self.assertAlmostEqual(r.x[1], 1.0, places=8)

    def test_diverges_above_two_over_L(self):
        Q = [[4.0, 0.0], [0.0, 1.0]]
        p = funcs.Quadratic(Q)
        # 증폭 인자는 |1 − αL| = 1.01 이므로 2000 회면 1.01^2000 ≈ 4×10^8 이 된다.
        r = uc.minimize(p, [1.0, 1.0], method='gd', step=2.01 / 4.0, tol=1e-12, maxiter=2000)
        self.assertFalse(r.converged)
        self.assertGreater(la.norm(r.x), 1e3)          # 실제로 터진다

    def test_rate_matches_theory(self):
        # 대각 이차형식에서 최적 고정스텝의 수렴 인자는 (κ−1)/(κ+1) 이다.
        kappa = 25.0
        Q = [[1.0, 0.0], [0.0, kappa]]
        p = funcs.Quadratic(Q)
        L, mu = kappa, 1.0
        r = uc.minimize(p, [1.0, 1.0], method='gd', step=2.0 / (L + mu),
                        tol=0.0, maxiter=60, keep_history=True)
        e0 = la.norm(r.history[0]['x'])
        e1 = la.norm(r.history[-1]['x'])
        k = len(r.history) - 1
        observed = (e1 / e0) ** (1.0 / k)
        self.assertAlmostEqual(observed, (kappa - 1) / (kappa + 1), places=6)

    def test_backtracking_gd_on_rosenbrock(self):
        p = funcs.Rosenbrock(2)
        r = uc.minimize(p, p.x0, method='gd', line_search='armijo', tol=1e-6, maxiter=60000)
        self.assertTrue(r.converged)
        self.assertLess(la.norm(la.vsub(r.x, [1.0, 1.0])), 1e-3)


class TestNewton(unittest.TestCase):
    def test_quadratic_one_step(self):
        Q = [[4.0, 1.0], [1.0, 3.0]]
        p = funcs.Quadratic(Q, [1.0, 2.0])
        r = uc.minimize(p, [5.0, -7.0], method='newton', tol=1e-12, maxiter=5)
        self.assertLessEqual(r.nit, 2)                 # 이차함수는 한 걸음
        self.assertLess(la.norm(p.grad(r.x)), 1e-10)

    def test_quadratic_convergence_rate(self):
        p = funcs.Rosenbrock(2)
        r = uc.minimize(p, [-1.2, 1.0], method='newton', tol=1e-13,
                        maxiter=100, keep_history=True)
        self.assertTrue(r.converged)
        # 이차수렴의 지문: 일단 수렴 영역에 들어오면 몇 걸음 만에 기계정밀도에 닿는다.
        gs = [h['gnorm'] for h in r.history]
        idx = next(i for i, v in enumerate(gs) if v < 1e-3)
        self.assertLess(gs[idx + 2], 1e-9,
                        '‖g‖ 1e-3 에서 두 걸음 안에 1e-9 아래로 가야 한다: %r' % gs[idx:idx + 3])

    def test_indefinite_hessian_handled(self):
        # 헤세가 부정부호인 지점에서 출발해도 하강해야 한다(수정 뉴턴).
        p = funcs.Rosenbrock(2)
        r = uc.minimize(p, [0.0, 1.0], method='newton', tol=1e-8, maxiter=200)
        self.assertTrue(r.converged)
        self.assertLess(p.f(r.x), 1e-12)


class TestQuasiNewton(unittest.TestCase):
    def test_bfgs_rosenbrock(self):
        p = funcs.Rosenbrock(2)
        r = uc.minimize(p, p.x0, method='bfgs', tol=1e-9, maxiter=500)
        self.assertTrue(r.converged)
        self.assertLess(la.norm(la.vsub(r.x, [1.0, 1.0])), 1e-6)

    def test_bfgs_beats_gd_in_iterations(self):
        p = funcs.Rosenbrock(2)
        b = uc.minimize(p, p.x0, method='bfgs', tol=1e-6, maxiter=5000)
        g = uc.minimize(p, p.x0, method='gd', line_search='armijo', tol=1e-6, maxiter=60000)
        self.assertLess(b.nit * 20, g.nit)

    def test_lbfgs_matches_bfgs(self):
        # n=10 로젠브록은 (−1,1,…,1) 근처에 국소 최소가 하나 더 있다. 두 방법 모두
        # 같은 곳으로 가야 한다 — 방향 계산이 같은 근사를 만든다는 뜻이다.
        p = funcs.Rosenbrock(10)
        a = uc.minimize(p, p.x0, method='bfgs', tol=1e-6, maxiter=2000)
        b = uc.minimize(p, p.x0, method='lbfgs', tol=1e-6, maxiter=2000, memory=8)
        self.assertTrue(a.converged, a.msg)
        self.assertTrue(b.converged, b.msg)
        self.assertLess(abs(a.fx - b.fx), 1e-8)
        self.assertLess(la.norm(la.vsub(a.x, b.x)), 1e-4)

    def test_bfgs_keeps_positive_definite(self):
        # BFGS 근사가 양의 정부호를 유지하면 방향은 언제나 하강 방향이다.
        p = funcs.Rosenbrock(2)
        r = uc.minimize(p, p.x0, method='bfgs', tol=1e-9, maxiter=500, keep_history=True)
        for h in r.history:
            self.assertLessEqual(h['gtd'], 1e-12)      # gᵀd ≤ 0


class TestConjugateGradient(unittest.TestCase):
    def test_linear_cg_exact_in_n_steps(self):
        n = 6
        A = [[0.0] * n for _ in range(n)]
        for i in range(n):
            for j in range(n):
                A[i][j] = 1.0 / (i + j + 1)
            A[i][i] += 1.0                              # 양의 정부호로 만든다
        b = [1.0] * n
        x, k = uc.cg_solve(A, b, tol=1e-14, maxiter=n)
        self.assertLessEqual(k, n)
        self.assertLess(la.norm(la.vsub(la.matvec(A, x), b)), 1e-9)

    def test_linear_cg_matches_direct(self):
        A = [[4.0, 1.0], [1.0, 3.0]]
        b = [1.0, 2.0]
        x, _ = uc.cg_solve(A, b, tol=1e-15, maxiter=10)
        y = la.solve(A, b)
        self.assertLess(la.norm(la.vsub(x, y)), 1e-10)

    def test_nonlinear_cg_rosenbrock(self):
        p = funcs.Rosenbrock(2)
        r = uc.minimize(p, p.x0, method='cg', tol=1e-8, maxiter=5000)
        self.assertTrue(r.converged)
        self.assertLess(la.norm(la.vsub(r.x, [1.0, 1.0])), 1e-5)


class TestTrustRegion(unittest.TestCase):
    def test_rosenbrock(self):
        p = funcs.Rosenbrock(2)
        r = uc.minimize(p, p.x0, method='tr', tol=1e-9, maxiter=500)
        self.assertTrue(r.converged)
        self.assertLess(la.norm(la.vsub(r.x, [1.0, 1.0])), 1e-6)

    def test_handles_negative_curvature(self):
        # 음의 곡률 방향이 있어도 신뢰영역은 경계까지 나아간다
        p = funcs.Rosenbrock(2)
        r = uc.minimize(p, [0.0, 1.0], method='tr', tol=1e-8, maxiter=500)
        self.assertTrue(r.converged)


class TestResultInvariants(unittest.TestCase):
    def test_monotone_decrease(self):
        # 라인서치를 쓰는 방법은 f 가 단조 감소해야 한다
        p = funcs.Rosenbrock(2)
        for m in ('gd', 'bfgs', 'cg', 'newton'):
            r = uc.minimize(p, p.x0, method=m, tol=1e-8, maxiter=3000,
                            line_search='armijo' if m == 'gd' else None,
                            keep_history=True)
            fs = [h['f'] for h in r.history]
            for i in range(len(fs) - 1):
                self.assertLessEqual(fs[i + 1], fs[i] + 1e-12, '%s 에서 f 가 증가했다' % m)

    def test_counts_are_consistent(self):
        p = funcs.Rosenbrock(2)
        r = uc.minimize(p, p.x0, method='bfgs', tol=1e-8, maxiter=500)
        self.assertGreaterEqual(r.nfev, r.nit)
        self.assertGreaterEqual(r.ngev, r.nit)


if __name__ == '__main__':
    unittest.main()
