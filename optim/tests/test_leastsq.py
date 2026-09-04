# -*- coding: utf-8 -*-
"""최소제곱 — 세 가지 해법이 같은 답을 주는가, 그리고 언제 갈라지는가."""
import math
import unittest

from py import leastsq as ls
from py import linalg as la


def close_vec(a, b, tol=1e-9):
    return la.norm(la.vsub(a, b)) <= tol * max(1.0, la.norm(a), la.norm(b))


class TestLinearLeastSquares(unittest.TestCase):
    def setUp(self):
        # y = 1 + 2x 위의 점 + 잡음 없음
        self.A = [[1.0, 1.0], [1.0, 2.0], [1.0, 3.0], [1.0, 4.0]]
        self.b = [3.0, 5.0, 7.0, 9.0]

    def test_three_methods_agree(self):
        x1 = ls.solve_normal(self.A, self.b)
        x2 = ls.solve_qr(self.A, self.b)
        x3 = ls.solve_svd(self.A, self.b)
        self.assertTrue(close_vec(x1, [1.0, 2.0], 1e-10))
        self.assertTrue(close_vec(x2, [1.0, 2.0], 1e-12))
        self.assertTrue(close_vec(x3, [1.0, 2.0], 1e-10))

    def test_residual_orthogonal(self):
        # 최적 잔차는 A 의 열공간에 직교한다 — 정규방정식의 기하학적 내용
        x = ls.solve_qr(self.A, self.b)
        r = la.vsub(la.matvec(self.A, x), self.b)
        for col in la.transpose(self.A):
            self.assertLess(abs(la.dot(col, r)), 1e-10)

    def test_qr_beats_normal_on_ill_conditioned(self):
        # Läuchli 행렬: eps^2 가 반올림에 묻히면 A^T A 가 특이해진다
        e = 1e-9
        A = [[1.0, 1.0], [e, 0.0], [0.0, e]]
        b = [2.0, 0.0, 0.0]
        exact = 2.0 / (2.0 + e * e)
        xq = ls.solve_qr(A, b)
        self.assertLess(abs(xq[0] - exact), 1e-8)
        with self.assertRaises(la.SingularMatrix):
            ls.solve_normal(A, b)

    def test_rank_deficient_min_norm(self):
        # 열이 중복이면 해가 무한히 많다. SVD 해법은 그중 최소노름 해를 준다.
        A = [[1.0, 1.0], [1.0, 1.0], [2.0, 2.0]]
        b = [1.0, 1.0, 2.0]
        x = ls.solve_svd(A, b)
        r = la.vsub(la.matvec(A, x), b)
        self.assertLess(la.norm(r), 1e-10)              # 잔차는 0
        self.assertAlmostEqual(x[0], x[1], places=10)   # 최소노름 → 두 성분이 같다
        self.assertLess(la.norm(x), la.norm([1.0, 0.0]) + 1e-10)

    def test_polyfit_exact(self):
        # 3차 다항식 위의 점 4개 → 정확히 복원
        coef = [2.0, -1.0, 0.5, 3.0]
        xs = [-1.0, 0.0, 1.0, 2.0]
        ys = [sum(c * x ** i for i, c in enumerate(coef)) for x in xs]
        got = ls.polyfit(xs, ys, 3)
        self.assertTrue(close_vec(got, coef, 1e-8))


class TestRidge(unittest.TestCase):
    def test_shrinks_toward_zero(self):
        A = [[1.0, 0.0], [0.0, 1.0]]
        b = [4.0, 2.0]
        x0 = ls.ridge(A, b, 0.0)
        x1 = ls.ridge(A, b, 1.0)
        self.assertTrue(close_vec(x0, [4.0, 2.0], 1e-10))
        self.assertTrue(close_vec(x1, [2.0, 1.0], 1e-10))       # 1/(1+lam) 배
        self.assertLess(la.norm(x1), la.norm(x0))

    def test_ridge_fixes_rank_deficiency(self):
        A = [[1.0, 1.0], [1.0, 1.0]]
        b = [2.0, 2.0]
        x = ls.ridge(A, b, 1e-3)                                # 특이해도 풀린다
        self.assertTrue(all(math.isfinite(v) for v in x))
        self.assertAlmostEqual(x[0], x[1], places=12)

    def test_ridge_matches_svd_filter(self):
        # 릿지 해는 SVD 로 s_i/(s_i^2+lam) 필터를 건 것과 같다
        A = [[3.0, 1.0], [1.0, 2.0], [0.0, 1.0]]
        b = [1.0, 2.0, 3.0]
        lam = 0.37
        x1 = ls.ridge(A, b, lam)
        U, s, V = la.svd(A)
        ub = la.matvec(la.transpose(U), b)
        coef = [s[i] / (s[i] ** 2 + lam) * ub[i] for i in range(len(s))]
        x2 = la.matvec(V, coef)
        self.assertTrue(close_vec(x1, x2, 1e-9))


class TestNonlinearLeastSquares(unittest.TestCase):
    def _exp_model(self):
        """y = a·exp(b·t) 자료. 참값 a=2.5, b=-0.7."""
        ts = [0.0, 0.3, 0.6, 1.0, 1.5, 2.0, 2.5, 3.0]
        ys = [2.5 * math.exp(-0.7 * t) for t in ts]

        def resid(p):
            return [p[0] * math.exp(p[1] * t) - y for t, y in zip(ts, ys)]

        def jac(p):
            return [[math.exp(p[1] * t), p[0] * t * math.exp(p[1] * t)] for t in ts]

        return resid, jac

    def test_gauss_newton_converges(self):
        resid, jac = self._exp_model()
        r = ls.gauss_newton(resid, jac, [1.0, -0.2], tol=1e-10, maxiter=200)
        self.assertTrue(r.converged, r.msg)
        self.assertAlmostEqual(r.x[0], 2.5, places=6)
        self.assertAlmostEqual(r.x[1], -0.7, places=6)

    def test_lm_converges_from_far(self):
        resid, jac = self._exp_model()
        far = [0.05, 2.0]                       # 가우스–뉴턴이 흔들리는 출발점
        r = ls.levenberg_marquardt(resid, jac, far, tol=1e-10, maxiter=500)
        self.assertTrue(r.converged, r.msg)
        self.assertAlmostEqual(r.x[0], 2.5, places=5)
        self.assertAlmostEqual(r.x[1], -0.7, places=5)

    def test_lm_handles_singular_jacobian(self):
        # J 가 랭크 부족이어도 감쇠 항 덕분에 방정식이 풀린다
        resid = lambda p: [p[0] + p[1] - 2.0, p[0] + p[1] - 2.0]
        jac = lambda p: [[1.0, 1.0], [1.0, 1.0]]
        r = ls.levenberg_marquardt(resid, jac, [0.0, 0.0], tol=1e-10, maxiter=100)
        self.assertLess(abs(r.x[0] + r.x[1] - 2.0), 1e-6)

    def test_jacobian_matches_numeric(self):
        from py import numdiff as nd
        resid, jac = self._exp_model()
        p = [1.7, -0.4]
        Ja, Jn = jac(p), nd.jacobian(resid, p)
        err = max(abs(Ja[i][j] - Jn[i][j]) for i in range(len(Ja)) for j in range(2))
        self.assertLess(err, 1e-6)

    def test_circle_fit(self):
        # 원 위의 점들 → 중심과 반지름을 되찾는다
        cx, cy, r0 = 1.5, -0.5, 2.0
        pts = [(cx + r0 * math.cos(t), cy + r0 * math.sin(t))
               for t in [0.0, 0.7, 1.4, 2.1, 2.8, 3.5, 4.2, 4.9, 5.6]]

        def resid(p):
            return [math.hypot(x - p[0], y - p[1]) - p[2] for x, y in pts]

        def jac(p):
            out = []
            for x, y in pts:
                d = math.hypot(x - p[0], y - p[1])
                out.append([-(x - p[0]) / d, -(y - p[1]) / d, -1.0])
            return out

        res = ls.levenberg_marquardt(resid, jac, [0.0, 0.0, 1.0], tol=1e-12, maxiter=300)
        self.assertTrue(res.converged)
        self.assertAlmostEqual(res.x[0], cx, places=6)
        self.assertAlmostEqual(res.x[1], cy, places=6)
        self.assertAlmostEqual(res.x[2], r0, places=6)


if __name__ == '__main__':
    unittest.main()


class TestExtras(unittest.TestCase):
    def test_chebyshev_better_conditioned(self):
        xs = [i / 29.0 for i in range(30)]
        for deg in (8, 12):
            mono = [[x ** k for k in range(deg + 1)] for x in xs]
            cheb = ls.chebyshev_design(xs, deg)
            self.assertLess(la.cond(cheb) * 100, la.cond(mono))

    def test_chebyshev_fits_same_function(self):
        xs = [i / 20.0 for i in range(21)]
        ys = [math.sin(3.0 * x) for x in xs]
        A = ls.chebyshev_design(xs, 8)
        c = ls.solve_qr(A, ys)
        self.assertLess(la.norm(ls.residual(A, c, ys)), 1e-6)

    def test_weighted_prefers_trusted_points(self):
        A = [[1.0], [1.0], [1.0]]
        b = [0.0, 0.0, 6.0]
        self.assertAlmostEqual(ls.weighted(A, b, [1.0, 1.0, 1.0])[0], 2.0, places=10)
        self.assertAlmostEqual(ls.weighted(A, b, [1.0, 1.0, 100.0])[0],
                               600.0 / 102.0, places=10)

    def test_huber_resists_outlier(self):
        # y = 2x 위의 점 + 이상치 하나
        xs = [1.0, 2.0, 3.0, 4.0, 5.0]
        ys = [2.0, 4.0, 6.0, 8.0, 50.0]
        A = [[x] for x in xs]
        ols = ls.solve_qr(A, ys)[0]
        rob = ls.huber_irls(A, ys, delta=1.0)[0]
        self.assertGreater(ols, 3.5)               # 최소제곱은 끌려간다
        self.assertLess(abs(rob - 2.0), 0.5)       # 후버는 버틴다

    def test_huber_equals_ols_without_outlier(self):
        xs = [1.0, 2.0, 3.0, 4.0]
        ys = [2.0, 4.0, 6.0, 8.0]
        A = [[x] for x in xs]
        self.assertAlmostEqual(ls.huber_irls(A, ys, delta=10.0)[0],
                               ls.solve_qr(A, ys)[0], places=10)

    def test_cgls_matches_qr(self):
        A = [[1.0, 1.0], [1.0, 2.0], [1.0, 3.0], [1.0, 4.5]]
        b = [3.1, 4.9, 7.2, 9.8]
        x, k = ls.solve_cg(A, b, tol=1e-14)
        y = ls.solve_qr(A, b)
        self.assertLess(la.norm(la.vsub(x, y)), 1e-9)
        self.assertLessEqual(k, 4 * len(A[0]))

    def test_cgls_never_forms_normal_matrix(self):
        # eps^2 가 반올림되는 영역에서도 CGLS 는 답을 준다
        e = 1e-9
        A = [[1.0, 1.0], [e, 0.0], [0.0, e]]
        b = [2.0, 0.0, 0.0]
        x, _ = ls.solve_cg(A, b, tol=1e-14, maxiter=50)
        self.assertLess(abs(x[0] - 1.0), 1e-6)
