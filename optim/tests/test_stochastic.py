# -*- coding: utf-8 -*-
"""확률적·대규모 최적화 — 잡음이 있어도 수렴하는가, 가속이 정말 빠른가."""
import math
import random
import unittest

from py import convex as cx
from py import funcs
from py import linalg as la
from py import stochastic as st


def make_ls(n=40, d=5, seed=0, noise=0.1):
    """최소제곱 문제를 표본 단위로 다룰 수 있게 만들어 둔다."""
    rng = random.Random(seed)
    w = [1.0, -2.0, 0.5, 0.3, -1.0][:d]
    X = [[rng.gauss(0, 1) for _ in range(d)] for _ in range(n)]
    y = [sum(a * b for a, b in zip(w, X[i])) + rng.gauss(0, noise) for i in range(n)]
    return X, y, w


class TestSGD(unittest.TestCase):
    def test_converges_with_decaying_step(self):
        X, y, w = make_ls(seed=1, noise=0.0)
        p = st.LeastSquaresBatch(X, y)
        r = st.sgd(p, [0.0] * len(w), step=lambda k: 0.5 / (1 + 0.02 * k),
                   epochs=400, seed=3)
        self.assertLess(la.norm(la.vsub(r.x, w)), 1e-2)

    def test_constant_step_stalls_in_a_ball(self):
        # 고정 보폭 SGD 는 최적해로 수렴하지 않고 그 주변을 맴돈다
        X, y, w = make_ls(seed=2, noise=0.3)
        p = st.LeastSquaresBatch(X, y)
        star = p.exact_solution()
        far = st.sgd(p, [0.0] * len(w), step=lambda k: 0.05, epochs=300, seed=5)
        near = st.sgd(p, [0.0] * len(w), step=lambda k: 0.005, epochs=300, seed=5)
        d_far = la.norm(la.vsub(far.x, star))
        d_near = la.norm(la.vsub(near.x, star))
        self.assertLess(d_near, d_far)          # 보폭이 작을수록 더 가까운 곳에서 맴돈다
        self.assertGreater(d_far, 1e-6)         # 정확히 도달하지는 않는다

    def test_minibatch_reduces_variance(self):
        X, y, w = make_ls(n=120, seed=4, noise=0.4)
        p = st.LeastSquaresBatch(X, y)
        star = p.exact_solution()
        d1 = la.norm(la.vsub(st.sgd(p, [0.0] * len(w), step=lambda k: 0.02,
                                    epochs=200, batch=1, seed=7).x, star))
        d16 = la.norm(la.vsub(st.sgd(p, [0.0] * len(w), step=lambda k: 0.02,
                                     epochs=200, batch=16, seed=7).x, star))
        self.assertLess(d16, d1)

    def test_gradient_is_unbiased(self):
        # 표본 기울기의 평균이 전체 기울기와 같아야 한다
        X, y, w = make_ls(n=30, seed=6)
        p = st.LeastSquaresBatch(X, y)
        x = [0.3, -0.2, 0.5, 0.1, 0.0]
        avg = [0.0] * len(x)
        for i in range(len(X)):
            g = p.grad_sample(x, [i])
            avg = la.vadd(avg, g)
        avg = la.vscale(1.0 / len(X), avg)
        self.assertLess(la.norm(la.vsub(avg, p.grad(x))), 1e-10)


class TestMomentum(unittest.TestCase):
    def test_momentum_beats_plain_on_ill_conditioned(self):
        Q = [[1.0, 0.0], [0.0, 100.0]]
        p = funcs.Quadratic(Q)
        x0 = [1.0, 1.0]
        n_plain = st.count_iters(p, x0, method='gd', tol=1e-8)
        n_mom = st.count_iters(p, x0, method='momentum', tol=1e-8)
        self.assertLess(n_mom * 2, n_plain)

    def test_nesterov_bound_holds(self):
        # 정리: f(x_k) − f* ≤ 2L‖x0−x*‖² / (k+1)²
        Q = [[1.0, 0.0], [0.0, 100.0]]
        p = funcs.Quadratic(Q, [1.0, 100.0])
        star, L = [1.0, 1.0], 100.0
        fstar = p.f(star)
        R2 = la.dot(star, star)
        r = st.accelerated(p, [0.0, 0.0], L=L, iters=300, keep_history=True)
        for k in (5, 10, 50, 100, 200):
            self.assertLessEqual(r.history[k]['f'] - fstar,
                                 2 * L * R2 / (k + 1) ** 2 + 1e-12)

    def test_accelerated_beats_plain_gradient(self):
        Q = [[1.0, 0.0], [0.0, 100.0]]
        p = funcs.Quadratic(Q, [1.0, 100.0])
        star = [1.0, 1.0]
        fstar = p.f(star)
        acc = st.accelerated(p, [0.0, 0.0], L=100.0, iters=200, keep_history=True)
        x = [0.0, 0.0]
        for _ in range(200):
            x = la.axpy(-1.0 / 100.0, p.grad(x), x)
        self.assertLess(acc.history[-1]['f'] - fstar, (p.f(x) - fstar) * 1e-3)

    def test_accelerated_is_not_monotone(self):
        # 가속법은 단조 감소하지 않는다 — 알려진 성질이자 흔한 오해
        Q = [[1.0, 0.0], [0.0, 100.0]]
        p = funcs.Quadratic(Q, [1.0, 100.0])
        r = st.accelerated(p, [0.0, 0.0], L=100.0, iters=300, keep_history=True)
        fs = [h['f'] for h in r.history]
        self.assertTrue(any(fs[i + 1] > fs[i] for i in range(len(fs) - 1)))


class TestAdaptive(unittest.TestCase):
    def test_adam_converges(self):
        X, y, w = make_ls(seed=8, noise=0.0)
        p = st.LeastSquaresBatch(X, y)
        r = st.adam(p, [0.0] * len(w), step=0.05, epochs=600, seed=2)
        self.assertLess(la.norm(la.vsub(r.x, w)), 5e-2)

    def test_adagrad_handles_scale_difference(self):
        # 좌표마다 스케일이 크게 다른 문제에서 AdaGrad 가 유리하다
        Q = [[1.0, 0.0], [0.0, 400.0]]
        p = funcs.Quadratic(Q, [1.0, 400.0])
        star = [1.0, 1.0]
        a = st.adagrad_full(p, [0.0, 0.0], step=1.0, iters=500)
        g = st.count_iters(p, [0.0, 0.0], method='gd', tol=1e-6, maxiter=500)
        self.assertLess(la.norm(la.vsub(a.x, star)), 1e-3)
        self.assertGreaterEqual(g, 400)

    def test_adam_bias_correction_matters_early(self):
        # 편향 보정은 초기 몇 에폭에서 차이를 만들고, 나중에는 사라진다
        X, y, _ = make_ls(n=200, seed=9, noise=0.1)
        p = st.LeastSquaresBatch(X, y)
        a1 = st.adam(p, [0.0] * 5, step=0.05, epochs=2, seed=1, bias_correct=True)
        b1 = st.adam(p, [0.0] * 5, step=0.05, epochs=2, seed=1, bias_correct=False)
        self.assertLess(a1.fx, b1.fx)                    # 초기에는 보정 쪽이 낫다
        a2 = st.adam(p, [0.0] * 5, step=0.05, epochs=100, seed=1, bias_correct=True)
        b2 = st.adam(p, [0.0] * 5, step=0.05, epochs=100, seed=1, bias_correct=False)
        self.assertLess(abs(a2.fx - b2.fx), 1e-9)        # 나중에는 같아진다


class TestProximal(unittest.TestCase):
    def _lasso(self):
        # 진짜 계수 중 셋이 0 인 희소 신호 — 라쏘가 그것을 찾아내는지 본다
        rng = random.Random(12)
        w = [1.5, 0.0, -2.0, 0.0, 0.0]
        X = [[rng.gauss(0, 1) for _ in range(5)] for _ in range(60)]
        y = [sum(a * b for a, b in zip(w, X[i])) + rng.gauss(0, 0.05)
             for i in range(60)]
        return X, y

    def test_ista_produces_sparse_solution(self):
        X, y = self._lasso()
        r = st.ista(X, y, lam=3.0, iters=5000)
        nz = [j for j, v in enumerate(r.x) if abs(v) > 1e-8]
        self.assertEqual(nz, [0, 2])               # 진짜 0 인 계수는 정확히 0 이 된다
        r0 = st.ista(X, y, lam=0.0, iters=5000)
        self.assertEqual(sum(1 for v in r0.x if abs(v) > 1e-8), 5)  # lam=0 이면 안 눌린다

    def _ill_lasso(self):
        # 열이 거의 평행한 설계행렬 — 조건수가 커야 가속의 차이가 드러난다
        rng = random.Random(5)
        d, n = 8, 40
        base = [[rng.gauss(0, 1) for _ in range(2)] for _ in range(n)]
        X = [[(base[i][0] if j < 4 else base[i][1]) + 0.02 * rng.gauss(0, 1)
              for j in range(d)] for i in range(n)]
        w = [1.0, 0, 0, 0, -1.5, 0, 0, 0]
        y = [sum(a * b for a, b in zip(w, X[i])) + rng.gauss(0, 0.05)
             for i in range(n)]
        return X, y

    def test_fista_faster_than_ista(self):
        X, y = self._ill_lasso()
        for iters in (200, 1000):
            a = st.ista(X, y, lam=0.3, iters=iters, keep_history=True)
            b = st.fista(X, y, lam=0.3, iters=iters, keep_history=True)
            self.assertLess(b.history[-1], a.history[-1] - 1e-6)

    def test_ista_matches_coordinate_descent(self):
        X, y = self._lasso()
        a = st.ista(X, y, lam=0.5, iters=20000)
        b = st.lasso_coordinate(X, y, lam=0.5, iters=500)
        self.assertLess(la.norm(la.vsub(a.x, b.x)), 1e-4)

    def test_admm_matches_ista(self):
        X, y = self._lasso()
        a = st.ista(X, y, lam=0.5, iters=20000)
        b = st.lasso_admm(X, y, lam=0.5, rho=1.0, iters=500)
        self.assertLess(la.norm(la.vsub(a.x, b.x)), 1e-4)

    def test_lam_zero_gives_least_squares(self):
        from py import leastsq as ls
        X, y = self._lasso()
        a = st.ista(X, y, lam=0.0, iters=20000)
        b = ls.solve_qr(X, y)
        self.assertLess(la.norm(la.vsub(a.x, b)), 1e-4)

    def test_soft_threshold_is_prox(self):
        # prox 의 정의를 직접 확인한다: argmin_z  lam|z| + (z−v)^2/2
        for v in (-2.0, -0.3, 0.0, 0.4, 3.0):
            for lam in (0.1, 0.5, 1.0):
                z = cx.soft_threshold([v], lam)[0]
                best, bz = None, None
                for k in range(-4000, 4001):
                    t = k * 0.001
                    val = lam * abs(t) + 0.5 * (t - v) ** 2
                    if best is None or val < best:
                        best, bz = val, t
                self.assertLess(abs(z - bz), 2e-3)


class TestSVRG(unittest.TestCase):
    def test_svrg_beats_sgd_with_constant_step(self):
        X, y, w = make_ls(n=100, seed=15, noise=0.2)
        p = st.LeastSquaresBatch(X, y)
        star = p.exact_solution()
        s = st.sgd(p, [0.0] * 5, step=lambda k: 0.02, epochs=200, seed=1)
        v = st.svrg(p, [0.0] * 5, step=0.02, epochs=40, seed=1)
        self.assertLess(la.norm(la.vsub(v.x, star)), la.norm(la.vsub(s.x, star)))


if __name__ == '__main__':
    unittest.main()
