# -*- coding: utf-8 -*-
"""제약 최적화 — KKT 조건이 실제로 성립하는지, 알고리즘이 그 점을 찾는지."""
import math
import unittest

from py import constrained as cs
from py import convex as cx
from py import funcs
from py import linalg as la


class TestEqualityQP(unittest.TestCase):
    """min ½xᵀGx + cᵀx  s.t. Ax = b  — KKT 선형계로 정확히 푼다."""

    def test_simple(self):
        G = [[2.0, 0.0], [0.0, 2.0]]
        c = [0.0, 0.0]
        A = [[1.0, 1.0]]
        b = [2.0]
        x, lam = cs.solve_eq_qp(G, c, A, b)
        self.assertAlmostEqual(x[0], 1.0, places=10)
        self.assertAlmostEqual(x[1], 1.0, places=10)
        # 정류조건: Gx + c + Aᵀλ = 0
        r = la.vadd(la.vadd(la.matvec(G, x), c), la.matvec(la.transpose(A), lam))
        self.assertLess(la.norm(r), 1e-10)

    def test_multiplier_is_sensitivity(self):
        # ∂p⋆/∂b = −λ  (감도 정리). 수치적으로 확인한다.
        G = [[2.0, 0.5], [0.5, 4.0]]
        c = [1.0, -2.0]
        A = [[1.0, 2.0]]
        h = 1e-6
        x0, lam = cs.solve_eq_qp(G, c, A, [3.0])
        def val(bv):
            x, _ = cs.solve_eq_qp(G, c, A, [bv])
            return 0.5 * la.dot(x, la.matvec(G, x)) + la.dot(c, x)
        num = (val(3.0 + h) - val(3.0 - h)) / (2 * h)
        self.assertAlmostEqual(num, -lam[0], places=6)

    def test_infeasible_constraint_raises(self):
        with self.assertRaises(la.SingularMatrix):
            cs.solve_eq_qp([[2.0, 0.0], [0.0, 2.0]], [0.0, 0.0],
                           [[1.0, 1.0], [2.0, 2.0]], [1.0, 3.0])


class TestKKTCheck(unittest.TestCase):
    def test_accepts_true_solution(self):
        # min x²+y² s.t. x+y ≥ 2  → 해 (1,1), λ = 2
        p = cs.Problem(f=lambda z: z[0] ** 2 + z[1] ** 2,
                       grad=lambda z: [2 * z[0], 2 * z[1]],
                       ineq=[lambda z: 2.0 - z[0] - z[1]],
                       ineq_grad=[lambda z: [-1.0, -1.0]])
        res = cs.kkt_residual(p, [1.0, 1.0], lam=[2.0])
        self.assertLess(max(res.values()), 1e-12)

    def test_rejects_wrong_multiplier(self):
        p = cs.Problem(f=lambda z: z[0] ** 2 + z[1] ** 2,
                       grad=lambda z: [2 * z[0], 2 * z[1]],
                       ineq=[lambda z: 2.0 - z[0] - z[1]],
                       ineq_grad=[lambda z: [-1.0, -1.0]])
        res = cs.kkt_residual(p, [1.0, 1.0], lam=[0.5])
        self.assertGreater(res['stationarity'], 1e-3)

    def test_negative_multiplier_flagged(self):
        p = cs.Problem(f=lambda z: z[0] ** 2, grad=lambda z: [2 * z[0]],
                       ineq=[lambda z: -z[0]], ineq_grad=[lambda z: [-1.0]])
        res = cs.kkt_residual(p, [0.0], lam=[-1.0])
        self.assertGreater(res['dual_feasibility'], 0.0)


class TestProjectedGradient(unittest.TestCase):
    def test_box_constrained(self):
        # min (x−3)² + (y+2)²  s.t.  −1 ≤ x,y ≤ 1  → 해 (1, −1)
        f = lambda z: (z[0] - 3.0) ** 2 + (z[1] + 2.0) ** 2
        g = lambda z: [2 * (z[0] - 3.0), 2 * (z[1] + 2.0)]
        proj = lambda z: cx.proj_box(z, -1.0, 1.0)
        r = cs.projected_gradient(f, g, proj, [0.0, 0.0], step=0.2,
                                  tol=1e-12, maxiter=5000)
        self.assertTrue(r.converged)
        self.assertAlmostEqual(r.x[0], 1.0, places=8)
        self.assertAlmostEqual(r.x[1], -1.0, places=8)

    def test_simplex_constrained(self):
        # min ‖x − v‖²  s.t.  x ∈ 단체  → 답은 투영 그 자체
        v = [0.8, -0.3, 0.9, 0.1]
        f = lambda z: sum((a - b) ** 2 for a, b in zip(z, v))
        g = lambda z: [2 * (a - b) for a, b in zip(z, v)]
        r = cs.projected_gradient(f, g, cx.proj_simplex, [0.25] * 4,
                                  step=0.4, tol=1e-14, maxiter=5000)
        want = cx.proj_simplex(v)
        self.assertLess(la.norm(la.vsub(r.x, want)), 1e-7)

    def test_fixed_point_is_optimum(self):
        # 최적점은 투영경사 사상의 고정점이다 (정리 7.4)
        v = [1.5, -0.4, 0.2]
        want = cx.proj_simplex(v)
        moved = cx.proj_simplex([a - 0.3 * 2 * (a - b) for a, b in zip(want, v)])
        self.assertLess(la.norm(la.vsub(moved, want)), 1e-12)


class TestPenaltyAndAugmented(unittest.TestCase):
    def _problem(self):
        # min x² + y²  s.t.  x + y = 2   → 해 (1,1), λ = −2 (Lagrangian 부호 규약에 따라)
        f = lambda z: z[0] ** 2 + z[1] ** 2
        g = lambda z: [2 * z[0], 2 * z[1]]
        h = lambda z: [z[0] + z[1] - 2.0]
        hj = lambda z: [[1.0, 1.0]]
        return f, g, h, hj

    def test_penalty_converges_as_mu_grows(self):
        f, g, h, hj = self._problem()
        errs = []
        for mu in (1.0, 10.0, 100.0, 1000.0):
            r = cs.penalty_method(f, g, h, hj, [0.0, 0.0], mu0=mu, growth=1.0,
                                  outer=1, tol=1e-12, maxiter=3000)
            errs.append(la.norm(la.vsub(r.x, [1.0, 1.0])))
        for i in range(len(errs) - 1):
            self.assertLess(errs[i + 1], errs[i])           # μ 를 키우면 가까워진다
        self.assertLess(errs[-1], 1e-2)

    def test_penalty_never_exactly_feasible(self):
        f, g, h, hj = self._problem()
        r = cs.penalty_method(f, g, h, hj, [0.0, 0.0], mu0=100.0, growth=1.0,
                              outer=1, tol=1e-12, maxiter=3000)
        self.assertGreater(abs(h(r.x)[0]), 1e-6)            # 항상 조금 위반한다

    def test_augmented_lagrangian_exact(self):
        f, g, h, hj = self._problem()
        r = cs.augmented_lagrangian(f, g, h, hj, [0.0, 0.0], mu0=1.0,
                                    outer=30, tol=1e-12, maxiter=3000)
        self.assertLess(la.norm(la.vsub(r.x, [1.0, 1.0])), 1e-8)
        self.assertLess(abs(h(r.x)[0]), 1e-8)               # 실행가능성이 회복된다
        self.assertAlmostEqual(r.lam[0], -2.0, places=6)

    def test_augmented_beats_penalty_at_same_mu(self):
        # 같은 벌 계수 μ=4 에서 비교한다. 페널티는 ν⋆/μ 만큼 어긋난 채 멈추지만,
        # 증강 라그랑주는 승수를 따로 들고 있어 그 짐을 벗는다.
        f, g, h, hj = self._problem()
        rp = cs.penalty_method(f, g, h, hj, [0.0, 0.0], mu0=4.0, growth=1.0,
                               outer=1, tol=1e-12, maxiter=3000)
        ra = cs.augmented_lagrangian(f, g, h, hj, [0.0, 0.0], mu0=4.0, growth=1.0,
                                     outer=20, tol=1e-12, maxiter=3000)
        self.assertAlmostEqual(ra.mu, 4.0, places=12)        # μ 를 키우지 않았다
        self.assertGreater(abs(h(rp.x)[0]), 0.3)             # 페널티는 크게 위반한 채로
        self.assertLess(abs(h(ra.x)[0]), 1e-8)               # AL 은 사실상 실행가능해진다
        self.assertLess(la.norm(la.vsub(ra.x, [1.0, 1.0])),
                        la.norm(la.vsub(rp.x, [1.0, 1.0])) * 1e-6)


class TestDuality(unittest.TestCase):
    def test_weak_duality_qp(self):
        # min ½xᵀx s.t. aᵀx ≥ 1 의 쌍대는 max ν − ν²‖a‖²/2, ν ≥ 0
        a = [3.0, 4.0]
        na2 = la.dot(a, a)
        primal = 0.5 / na2                                   # 원문제 최적값
        for nu in (0.0, 0.01, 0.05, 1.0 / na2, 0.1, 0.5):
            dual = nu - 0.5 * nu * nu * na2
            self.assertLessEqual(dual, primal + 1e-12)       # 약쌍대성
        self.assertAlmostEqual((1.0 / na2) - 0.5 * (1.0 / na2) ** 2 * na2,
                               primal, places=12)            # 강쌍대성(Slater)

    def test_dual_function_is_concave(self):
        # g(λ) = inf_x L(x,λ) 는 λ 에 대해 오목 — 무작위 현으로 확인
        import random
        rng = random.Random(0)
        G = [[2.0, 0.0], [0.0, 4.0]]
        A = [[1.0, 1.0]]
        b = [1.0]

        def dual(lam):
            # inf_x ½xᵀGx + λᵀ(Ax − b) = −½ (Aᵀλ)ᵀ G⁻¹ (Aᵀλ) − λᵀb
            v = la.matvec(la.transpose(A), lam)
            return -0.5 * la.dot(v, la.solve(G, v)) - la.dot(lam, b)

        for _ in range(200):
            l1 = [rng.uniform(-5, 5)]
            l2 = [rng.uniform(-5, 5)]
            t = rng.random()
            mid = [t * l1[0] + (1 - t) * l2[0]]
            self.assertGreaterEqual(dual(mid) + 1e-12,
                                    t * dual(l1) + (1 - t) * dual(l2))


if __name__ == '__main__':
    unittest.main()
